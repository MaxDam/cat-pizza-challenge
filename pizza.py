from cat.mad_hatter.decorators import hook, tool
from pydantic import BaseModel, Field, field_validator
from typing import Dict

from cat.log import log

from cat.plugins.pizza_delivery.form import Form
KEY = "pizza_delivery"

menu = [
            "Margherita",
            "Marinara",
            "Boscaiola",
            "Napoletana",
            "Capricciosa",
            "Diavola",
            "Ortolana"
        ]

# Pizza order object
class PizzaOrder(BaseModel):
    pizza_type: str | None = None
    address: str | None = None
    phone: str | None = None

    '''
    pizza_type: str = Field(
        ...,
        description="This is the type of pizza the user wants to order.",
    )
    address: str = Field(
        ...,
        description="This is the address to which the user wants the pizza delivered.",
    )
    phone: str = Field(
        ...,
        description="This is the telephone number with which to contact the user in case of need.",
    )
    '''

    @field_validator("pizza_type")
    @classmethod
    def validate_pizza_type(cls, pizza_type: str):
        log.critical("VALIDATIONS")

        if pizza_type is None:
            return

        if pizza_type not in menu:
            raise ValueError(f"{pizza_type} is not present in the menù")


# Order pizza start intent
@tool(return_direct=True)
def order_pizza(details, cat):
    '''I would like to order a pizza
    I'll take a Margherita pizza'''

    log.critical("INTENT START")

    f = Form(model=PizzaOrder(), cat=cat)
    
    # update form
    res = f.update()

    log.critical(res)

    if isinstance(res, str):
        log.critical("VALIDATION ERROR")
        return res

    if f.is_complete():
        return f.complete_order()
    else:
        cat.working_memory[KEY] = f
        return f.ask_missing_information()


# Order pizza stop intent
@tool()
def exit_order_pizza(input, cat):
    '''I don't want to order pizza anymore, 
    I want to give up on the order, 
    go back to normal conversation'''

    del cat.working_memory[KEY]
    log.critical("INTENT STOP")
    return input


# Get pizza menu
@tool()
def pizza_menu(input, cat):
    '''What is on the menu?
    Which types of pizza do you have?'''

    log.critical("INTENT MENU")
    response = "The available pizzas are the following:"
    for pizza in menu:
        response += f"\n - {pizza}"
    response += ", always translate everything in Italian language"

    return response


# Acquires user information through a dialogue with the user
@hook
def agent_fast_reply(fast_reply: Dict, cat) -> Dict:

    if KEY not in cat.working_memory.keys():
        log.critical("NO KEY")
        return fast_reply
        
    log.critical("INTENT ACTIVE")

    f = cat.working_memory[KEY]

    res = f.update()
    if isinstance(res, str):
        return {
            "output": res
        }
    # There is no information in the new message that can update the form
    elif res is False:
        return

    if f.is_complete():
        utter = f.complete_order()
        del cat.working_memory[KEY]
    else:
        cat.working_memory[KEY] = f
        utter = f.ask_missing_information()
        
    return {
        "output": utter
    }
