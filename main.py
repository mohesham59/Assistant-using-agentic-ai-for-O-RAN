import os
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.prompts import PromptTemplate
from tools.guidelines import guidelines_engine
from tools.web_reader import web_reader_engine
from tools.report_generator import generate_report
import config
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# تحميل الـ .env
load_dotenv()

# Prompt Template لتوليد تقرير شامل
report_prompt = PromptTemplate(
    """
    You are an expert content optimizer with access to a guidelines document and web data. Based on the user input and all available data from the provided tools (guidelines_engine and web_reader_engine), generate a comprehensive Content Optimization Report in Markdown format. The report should be as detailed as possible, with no limit on length, and include:

    1. **Introduction**:
       - Explain the purpose of the report.
       - Summarize the user input and its context.
       - Outline the scope of the analysis based on the provided guidelines and web data.

    2. **Detailed Analysis**:
       - Analyze the content thoroughly using all relevant information from the guidelines (guidelines_engine) and web data (web_reader_engine).
       - Identify all potential issues in the content (e.g., structure, clarity, terminology, engagement, etc.).
       - For each issue, provide a detailed explanation, including:
         - Why the issue affects the content's effectiveness.
         - Specific examples or references from the guidelines or web data.
         - Potential impact on the target audience.

    3. **Recommendations**:
       - For each identified issue, provide a detailed recommendation, including:
         - A clear explanation of why the recommendation is important.
         - Step-by-step instructions for implementing the recommendation.
         - At least one specific, practical example to illustrate the recommendation.
         - Any relevant references to the guidelines or web data to support the recommendation.

    4. **Conclusion**:
       - Summarize the key findings and recommendations.
       - Highlight the benefits of implementing the recommendations.
       - Provide a final statement on how the optimized content will improve user experience and achieve its goals.

    Use all available data from the guidelines_engine and web_reader_engine to ensure the report is comprehensive. Format the report in professional Markdown with clear headings, subheadings, bullet points, and examples. Ensure the output is suitable for conversion to a PDF.

    User Input: {user_input}
    """
)

# إعداد الـ Agent
agent = ReActAgent.from_tools(
    tools=[
        guidelines_engine,
        web_reader_engine,
        generate_report
    ],
    llm=Settings.llm,
    verbose=True
)

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    try:
        # استخدام الـ prompt المخصص لتوليد التقرير
        response = agent.chat(report_prompt.format(user_input=user_input))
        logger.info(f"Agent response: {str(response)[:100]}...")
        # حفظ التقرير كـ PDF
        report_result = generate_report(str(response), "report.pdf")
        logger.info(f"Report generation result: {report_result}")
        print("Agent: ", response)
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        print(f"Error: {str(e)}")