
from langchain.prompts.prompt import PromptTemplate


DOCUMENT_TOOL_DESCRIPTION = (
    "Searches and returns texts regarding Terms and conditions documents for car brands "
    "cover essential information related to vehicle ownership. This includes details on "
    "warranties, maintenance requirements, usage restrictions, ownership transfer procedures, "
    "liability disclaimers, termination of services, privacy and data collection policies, "
    "compliance with laws, intellectual property rights, customer responsibilities, and dispute "
    "resolution processes. It's crucial for car owners to carefully review these documents to "
    "understand their rights and obligations."
)

SEARCH_TOOL_DESCRIPTION = (
    "If you cannot find the answer in LLC documents and the user query is related to vehicles "
    "then Use this to lookup information from google search engine and if the query isn't "
    "related to the vehicles and its finance just don't use this tool and answer with that "
    "kindly ask only about vehicles information as we deal only vehicles."
)


SQL_TOOL_DESCRIPTION = """If question is ask about the car/vehicles information which is in inventory then
use this tool. You have a database named, inventory360 and a table named, inventorylog. Search the records
here and gives the answer with brief details of the car or cars as the sales manager does. Dont answer like Yes
 or no we have or dont have etc.
 In case the query Result is empty or you dont find any relevent data in the inventory then recommend similar
 cars to the customer by querying again by altering the make, model or year"""

_DEFAULT_TEMPLATE = """Given an input question, first create a postgres syntactically correct {dialect} query to run, 
then look at the results of the query and return the answer.
Use the following format:

Question: "Question here"
SQLQuery: "SQL Query to run"
SQLResult: "Result of the SQLQuery"
Answer: "Final answer here"

Only use the following tables:

{table_info}
schema_description = "Schema Information for InventoryLog:\n"
    columns_info = [
        {'name': 'Id', 'type': 'INTEGER', 'constraints': 'NOT NULL IDENTITY(1,1) PRIMARY KEY'},
        {'name': 'StoreId', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'ActualLocation', 'type': 'VARCHAR(500)', 'constraints': 'NULL'},
        {'name': 'PurchaseDate', 'type': 'DATE', 'constraints': 'NULL'},
        {'name': 'CheckInDate', 'type': 'DATE', 'constraints': 'NULL'},
        {'name': 'Year', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'Make', 'type': 'VARCHAR(50)', 'constraints': 'NULL'},
        {'name': 'Model', 'type': 'VARCHAR(50)', 'constraints': 'NULL'},
        {'name': 'Trim', 'type': 'VARCHAR(50)', 'constraints': 'NULL'},
        {'name': 'BodyTypeId', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'InteriorColorId', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'ExteriorColorId', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'MilesIn', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'MileOut', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'Doors', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'Cylenders', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'FuelTypeId', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'DriveTrainId', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'AvailablityId', 'type': 'INTEGER', 'constraints': 'NULL'},
        {'name': 'SoldDate', 'type': 'DATETIME', 'constraints': 'NULL'},
        {'name': 'IsLuxury', 'type': 'BIT', 'constraints': 'NULL'}
    ]
If someone asks for the table Car/Vehicles, they really mean the InventoryLog table.
Always put semicolon at the end of the query.
Question: {input}"""

PROMPT = PromptTemplate(
    input_variables=["input", ], template=_DEFAULT_TEMPLATE
)
examples = [
    {"input": "List all Cars/Vehicles.", "query": "SELECT * FROM InventoryLog;"},

    {
        "input": "Find the total Milage of all cars/vehicles.",
        "query": "SELECT SUM(MilesIn) FROM InventoryLog;",
    },
    {
        "input": "List all honda cars.",
        "query": "SELECT * FROM InventoryLog WHERE Make = 'honda';",
    },
    {
        "input": "How many cars are there in the store with ID 5?",
        "query": "SELECT COUNT(*) FROM InventoryLog WHERE StoreId = 5;",
    },
    {
        "input": "Find the total number of cars/vehicles.",
        "query": "SELECT COUNT(*) FROM InventoryLog;",
    },
    {
        "input": "List all cars/vehicles that have milage more than 1000 miles.",
        "query": "SELECT * FROM InventoryLog WHERE MilesIn > 1000;",
    },
    {
        "input": "Which cars are from the year 2000?",
        "query": "SELECT * FROM InventoryLog WHERE strftime('%Y', Year) = '2000';",
    },
]