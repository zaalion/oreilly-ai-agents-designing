import asyncio
import logging

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.utils.logging import setup_logging


class RestaurantPlugin:
    """
    A simple plugin that exposes Python functions to Semantic Kernel.
    The model can decide when to call these functions.
    """

    def __init__(self):
        self.restaurants = [
            {
                "name": "Persian Grill",
                "city": "NYC",
                "cuisine": "Persian",
                "rating": 4.7,
                "price": "$$",
            },
            {
                "name": "Sushi Central",
                "city": "Toronto",
                "cuisine": "Japanese",
                "rating": 4.5,
                "price": "$$$",
            },
            {
                "name": "Pasta House",
                "city": "Chicago",
                "cuisine": "Italian",
                "rating": 4.3,
                "price": "$$",
            },
            {
                "name": "Kebab Palace",
                "city": "Florida",
                "cuisine": "Persian",
                "rating": 4.6,
                "price": "$$",
            },
        ]

    @kernel_function(
        name="find_restaurants",
        description="Finds restaurants by city and cuisine.",
    )
    def find_restaurants(self, city: str, cuisine: str) -> str:
        matches = []

        for restaurant in self.restaurants:
            if (
                restaurant["city"].lower() == city.lower()
                and restaurant["cuisine"].lower() == cuisine.lower()
            ):
                matches.append(restaurant)

        if not matches:
            return f"No {cuisine} restaurants found in {city}."

        return str(matches)

    @kernel_function(
        name="get_top_rated_restaurant",
        description="Gets the highest-rated restaurant in a city.",
    )
    def get_top_rated_restaurant(self, city: str) -> str:
        matches = [
            restaurant
            for restaurant in self.restaurants
            if restaurant["city"].lower() == city.lower()
        ]

        if not matches:
            return f"No restaurants found in {city}."

        top_restaurant = max(matches, key=lambda restaurant: restaurant["rating"])

        return str(top_restaurant)


async def main() -> None:
    # Optional logging
    setup_logging()
    logging.getLogger("semantic_kernel").setLevel(logging.INFO)

    # Create the kernel
    kernel = Kernel()

    # Add your Azure AI Foundry / Azure OpenAI deployed GPT model
    chat_completion = AzureChatCompletion(
        deployment_name="gpt-4o",  # Your deployment name
        endpoint="https://agentic-or-foundry.openai.azure.com/",
        api_key="YOUR_API_KEY",
        api_version="2024-10-21",
    )

    kernel.add_service(chat_completion)

    # Add the plugin to the kernel
    kernel.add_plugin(
        RestaurantPlugin(),
        plugin_name="RestaurantPlugin",
    )

    # Enable automatic function calling
    execution_settings = PromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create chat history
    history = ChatHistory()
    history.add_system_message(
        """
        You are a helpful restaurant assistant.
        Use the available functions when the user asks about restaurants.
        Explain your answer clearly and briefly.
        """
    )

    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("User > ")

        if user_input.lower() == "exit":
            break

        history.add_user_message(user_input)

        result = await chat_completion.get_chat_message_content(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel,
        )

        print(f"Assistant > {result}\n")

        history.add_message(result)


if __name__ == "__main__":
    asyncio.run(main())