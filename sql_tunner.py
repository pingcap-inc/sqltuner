import os
from dotenv import load_dotenv, find_dotenv
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

class SqlTunner:
    def __init__(self):
        self.init_dotenv()
        self.chat = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k")
        self.init_output_parser()
        self.init_prompt()

    def init_dotenv(self):
        _ = load_dotenv(find_dotenv())

    def init_output_parser(self):
        response_schemas = [
            ResponseSchema(name="tuned_sql", description="The SQL after optimization"),
            ResponseSchema(name="what_changed", description="Description of the changes made and why you made them, if nothing changed, just return None"),
            ResponseSchema(name="index_suggestion", description="Recommendations for indexes to improve performance, if no recommendations, just return None"),
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

    def init_prompt(self):
        template = """
            Your goal is to fine-tune the provided SQL statement to run fast on TiDB \
            while ensuring it retains the same semantics as the original one. \
            You will receive the SQL statement along with the relevant table schemas and statistics information, all enclosed within three backquotes (```). \
            If the schemas or statistics information are not provided, you can assume that they are not available. \
            sql statement: ```{original_sql}```,
            schemas: ```{schemas}```,
            statistics information: ```{stats_info}```,\n
            {format_instructions}
        """
        self.prompt = ChatPromptTemplate(
            messages = [
                HumanMessagePromptTemplate.from_template(template),
            ],
            input_variables = ["original_sql", "schemas", "stats_info"],
            partial_variables = {"format_instructions": self.output_parser.get_format_instructions()},
        )

    def tune(self, original_sql, schemas, stats_info):
        input = self.prompt.format_prompt(original_sql=original_sql, schemas=schemas, stats_info=stats_info)
        print(input.to_messages())
        try:
            output = self.chat(input.to_messages())
            print(output.content)
            return self.output_parser.parse(output.content)
        except Exception as e:
            print(e)    
            raise
    


