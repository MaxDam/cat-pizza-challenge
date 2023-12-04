import json
from cat.log import log
from langchain.chains import create_tagging_chain_pydantic
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from kor import create_extraction_chain, from_pydantic, Object, Text

class ConversationalForm:

    def __init__(self, model, cat, lang):
        self.model = model
        self.cat = cat
        self.language = lang


    # Check if the form is completed
    def is_completed(self):
        for k,v in self.model.model_dump().items():
            if v in [None, ""]:
                return False
        return True


    # Return list of empty form's fields
    def _check_what_is_empty(self):
        ask_for = []
        for field, value in self.model.model_dump().items():
            if value in [None, "", 0]:
                ask_for.append(f'{field}')
        return ask_for


    # Queries the llm asking for the missing fields of the form
    def ask_missing_information(self):

        # Gets the information it should ask the user based on the fields that are still empty
        ask_for = self._check_what_is_empty()

        prefix = self.cat.mad_hatter.execute_hook("agent_prompt_prefix",'')
        user_message = self.cat.working_memory["user_message_json"]["text"]
        chat_history = self.cat.agent_manager.agent_prompt_chat_history(
            self.cat.working_memory["history"]
        )
        
        # Prompt
        prompt = f"""{prefix}
        Create a question for the user (translating everything in {self.language} language), 
        below are some things to ask the user in a conversational and confidential way, to complete the pizza order.
        You should only ask one question at a time even if you don't get all the information
        don't ask how to list! Don't say hello to the user! Don't say hi.
        Explain that you need some information. If the ask_for list is empty, thank them and ask how you can help them
        ### ask_for list: {ask_for}
        {chat_history}
        Human: {user_message}
        AI: 
        """

        print(f'ask_missing_information:\n{ask_for}')
        llm_question = self.cat.llm(prompt)
        return llm_question 


    # Updates the form with the information extracted from the user's response
    def update_from_user_response(self):

        # Extract new info
        #user_response_json = self._extract_info_from_scratch()
        #user_response_json = self._extract_info_by_pydantic()
        user_response_json = self._extract_info_by_kor()

        # Gets a new_model with the new fields filled in
        non_empty_details = {k: v for k, v in user_response_json.items() if v not in [None, ""]}
        new_model = self.model.copy(update=non_empty_details)

        # Check if there is no information in the new_model that can update the form
        if new_model.model_dump() == self.model.model_dump():
            return False

        # Validate new_model (raises ValidationError exception on error)
        self.model.model_validate(new_model.model_dump())

        # Overrides the current model with the new_model
        self.model = self.model.model_construct(**new_model.model_dump())
        print(f'updated model:\n{self.model.model_dump_json(indent=4)}')
        return True



    # Extracted new informations from the user's response (by pydantic)
    def _extract_info_by_pydantic(self):
        parser = PydanticOutputParser(pydantic_object=type(self.model))
        prompt = PromptTemplate(
            template="Answer the user query.\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        print(f'get_format_instructions:\n{parser.get_format_instructions()}')
        
        user_message = self.cat.working_memory["user_message_json"]["text"]
        _input = prompt.format_prompt(query=user_message)
        output = self.cat.llm(_input.to_string())
        print(f"output: {output}")

        #user_response_json = parser.parse(output).dict()
        user_response_json = json.loads(output)
        print(f'user response json:\n{user_response_json}')
        return user_response_json


    # Extracted new informations from the user's response (by kor)
    def _extract_info_by_kor(self):
        schema, validator = from_pydantic(type(self.model))   
        chain = create_extraction_chain(self.cat._llm, schema, encoder_or_encoder_class="json", validator=validator)
        user_message = self.cat.working_memory["user_message_json"]["text"]
        output = chain.run(user_message)["validated_data"]
        user_response_json = output.dict()
        print(f'user response json:\n{user_response_json}')
        return user_response_json


    # Extracted new informations from the user's response (from sratch)
    def _extract_info_from_scratch(self):

        # Prompt
        user_message = self.cat.working_memory["user_message_json"]["text"]
        prompt = f"""Update the following JSON with information extracted from the Sentence:

        Sentence: I want to order a pizza
        JSON:{{
            "pizza_type": null,
            "address": null,
            "phone": null
        }}
        UPDATED JSON:{{
            "pizza_type": null,
            "address": null,
            "phone": null
        }}

        Sentence: I live in Via Roma 1
        JSON:{{
            "pizza_type": "Margherita",
            "address": null,
            "phone": null
        }}
        Updated JSON:{{
            "pizza_type": "Margherita",
            "address": "Via Roma 1",
            "phone": null
        }}

        Sentence: {user_message}
        JSON:{self.model.model_dump_json(indent=4)}
        Updated JSON:"""
        
        json_str = self.cat.llm(prompt)
        user_response_json = json.loads(json_str)
        print(f'user response json:\n{user_response_json}')
        return user_response_json


# TODO:
# https://www.askmarvin.ai/welcome/what_is_marvin/
# https://github.com/jxnl/instructor
