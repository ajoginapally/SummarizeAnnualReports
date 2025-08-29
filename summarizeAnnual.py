import os
import json
from datetime import datetime
from typing import List, Optional

import PyPDF2
#from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from markdown2 import markdown
from weasyprint import HTML

load_dotenv()

def load_file(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return "".join(page.extract_text() or "" for page in reader.pages)



class AnnualReportSummary(BaseModel):
    company_name: str = Field(..., description="Name of the company")
    cik: str = Field(..., description="CIK indentifier  assigned by the SEC")
    filing_date: datetime = Field(..., description="Date when the report was filed")
    fiscal_year: datetime = Field(..., description="Fiscal year of the report")
    total_revenue: Optional[float] = Field(..., description="Total revenue for the fiscal year in USD")
    net_income: Optional[float] = Field(..., description="Net income for the fiscal year in USD")
    total_assets: Optional[float] = Field(..., description="Total assets at the end of the fiscal year in USD")
    total_liabilities: Optional[float] = Field(..., description="Total liabilities at the end of the fiscal year in USD")
    operating_cash_flow: Optional[float] = Field(..., description="Operating cash flow for the fiscal year in USD")
    cash_and_equivalents: Optional[float] = Field(..., description="Cash and cash equivalents at the end of the fiscal year in USD")
    num_employees: int = Field(..., description="Number of employees at the end of the fiscal year")
    auditor: Optional[str] = Field(..., description="Name of the external auditor")
    business_description: Optional[str] = Field(..., description="Description of the company's business")
    market_cap: Optional[float] = Field(None, description="Market capitalization at the end of the fiscal year in USD")
    stock_price: Optional[float] = Field(None, description="Stock price at the end of the fiscal year in USD")
    management_discussion: Optional[str] = Field(..., description="Summary of management's discussion and analysis")
    eps: Optional[float] = Field(..., description="Earnings per share for the fiscal year in USD")
    key_highlights: Optional[List[str]] = Field(..., description="List of key highlights from the report")
    risks: Optional[List[str]] = Field(..., description="List of major risks mentioned in the report")
    future_outlook: Optional[str] = Field(..., description="Summary of the company's future outlook")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
schema = json.dumps(AnnualReportSummary.model_json_schema(), indent=2)
report = load_file("reportPDFS/nvidia_10k.pdf")
prompt = f'Analyze the following 10-K annual report and extract the relevant financial and business information. Fill the data model absed on it, Annual Report Text:\n\n{report}'
prompt += f'The output needs to be in the following data format:\n\n{schema}\n\nNo extra fields allowed'

response = client.models.generate_content(
    model = 'gemini-2.0-flash',
    contents = prompt,
    config = {
        'reponse_mime_type': 'application/json',
        'response_schema': AnnualReportSummary
    }
)

ar = AnnualReportSummary.model_validate_json(response.text)
print(ar)

md_lines = [
    f"# {ar.company_name} Annual Report {ar.fiscal_year_end.year}",
    f"**CIK:** {ar.cik}",
    f"**Fiscal Year End:** {ar.fiscal_year_end.strftime('%Y-%m-%d')}",
    f"**Filing Date:** {ar.filing_date.strftime('%Y-%m-%d')}",
    "## Financials"
]

if ar.total_revenue is not None:
    md_lines.append(f"- **Total Revenue:** ${ar.total_revenue:,.2f}")
if ar.net_income is not None:
    md_lines.append(f"- **Net Income:** ${ar.net_income:,.2f}")
if ar.total_assets is not None:
    md_lines.append(f"- **Total Assets:** ${ar.total_assets:,.2f}")
if ar.total_liabilities is not None:
    md_lines.append(f"- **Total Liabilities:** ${ar.total_liabilities:,.2f}")
if ar.operating_cash_flow is not None:
    md_lines.append(f"- **Operating Cash Flow:** ${ar.operating_cash_flow:,.2f}")
if ar.cash_and_equivalents is not None:
    md_lines.append(f"- **Cash & Equivalents:** ${ar.cash_and_equivalents:,.2f}")
if ar.num_employees is not None:
    md_lines.append(f"- **Number of Employees:** {ar.num_employees}")
if ar.auditor:
    md_lines.append(f"- **Auditor:** {ar.auditor}")

if ar.business_description:
    md_lines += ["\n## Business Description", ar.business_description]
if ar.risk_factors:
    md_lines += ["\n## Risk Factors"] + [f"- {rf}" for rf in ar.risk_factors]
if ar.management_discussion:
    md_lines += ["\n## Management Discussion & Analysis", ar.management_discussion]

md = "\n\n".join(md_lines)
html = markdown(md)
company = ar.company_name.replace(" ", "_")
filename = f"annual_report_{company}_{ar.fiscal_year_end.year}.pdf"
HTML(string=html).write_pdf(filename)