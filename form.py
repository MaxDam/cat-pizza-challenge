import json
from cat.log import log
from pydantic import ValidationError

class Form:

    def __init__(self, model, cat):
        self.model = model
        self.cat = cat


    # Check if the order is complete
    def is_complete(self):
        for k,v in self.model.model_dump().items():
            if v is None:
                return False
        return True


    # Complete the order
    def complete_order(self):
        return f"""
        ╔═════════════════════════════════════════════════════════════════════╗
        ║                  PIZZA CHALLENGE - ORDER COMPLETED                  ║
        ╚═════════════════════════════════════════════════════════════════════╝
        {self.model.model_dump_json()}
        """


    # Return list of empty form's fields
    def check_what_is_empty(self):
        ask_for = []
        for field, value in self.model.model_dump().items():
            if value in [None, "", 0]:
                ask_for.append(f'{field}')
        return ask_for


    # Queries the llm asking for the missing fields of the form
    def ask_missing_information(self):

        # Gets the information it should ask the user based on the fields that are still empty
        ask_for = self.check_what_is_empty()

        user_message = self.cat.working_memory["user_message_json"]["text"]
        chat_history = self.cat.agent_manager.agent_prompt_chat_history(
            self.cat.working_memory["history"]
        )
        prefix = self.cat.mad_hatter.execute_hook("agent_prompt_prefix",'')

        # Prompt
        prompt = f"""{prefix}
        Create a question for the user (translating everything into Italian), 
        below are some things to ask the user in a conversational and confidential way, to complete the pizza order.
        You should only ask one question at a time even if you don't get all the information
        don't ask how to list! Don't say hello to the user! Don't say hi.
        Explain that you need some information. If the ask_for list is empty, thank them and ask how you can help them
        ### ask_for list: {ask_for}
        """

        print(f'ask_missing_information:\n{ask_for}')
        question = self.cat.llm(prompt)
        return question 


    # Updates the form with the information extracted from the user's response
    def update(self):

        # Extract new info
        details = self._extract_info()
        print(f'_extract_info:\n{details}')

        # Gets a new order with the new fields filled in
        non_empty_details = {k: v for k, v in details.items() if v not in [None, ""]}
        new_details = self.model.copy(update=non_empty_details).model_dump()

        # Check if there is no information in the new message that can update the form
        if new_details == self.model.model_dump():
            return False

        # Validate form
        try:
            self.model.model_validate(new_details)
        except ValidationError as e:
            for error_message in e.errors():
                return error_message["msg"]

        # Update form
        self.model = self.model.model_construct(**new_details)
        print(f'update:\n{self.model.model_dump_json(indent=4)}')
        return True


    # Extracted new informations from the user's response
    def _extract_info(self):

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
        return json.loads(json_str)
