import os
import sys
import json
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

_cerebras = OpenAI(api_key=os.environ.get("CEREBRAS_API_KEY"), base_url="https://api.cerebras.ai/v1")
_openrouter = OpenAI(api_key=os.environ.get("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")

PROVIDERS = [
    {"client": _cerebras,   "model": "gpt-oss-120b",            "name": "Cerebras"},
    {"client": _openrouter, "model": "openai/gpt-oss-120b:free", "name": "OpenRouter"},
]
MCP_SERVER = os.path.join(os.path.dirname(__file__), "mcp_server.py")

SYSTEM = """You are a SQL expert for a university library PostgreSQL database.

STRICT WORKFLOW — follow every time:
1. list_tables   → see all available tables
2. describe_table → check EXACT column names for every table you will use
3. run_query     → execute your SQL
4. If run_query returns error → describe_table again, fix SQL, retry

PostgreSQL rules (important):
- Overdue (still out): return_date IS NULL AND due_date < CURRENT_DATE
- Late returns: return_date > due_date
- "Members"/"borrowers" = Student + Faculty → use UNION ALL
- Loans & Reservations link via: borrower_type ('Student' or 'Faculty') + borrower_id
- Month grouping: TO_CHAR(date_col, 'YYYY-MM')
- Last N months: col >= CURRENT_DATE - INTERVAL 'N months'
- Fine has NO student_id/faculty_id → always join through Loan
- PurchaseOrderItem has NO supplier_id → join through PurchaseOrder

Exact status values (case-sensitive):
- fine.status: 'Paid', 'Unpaid', 'Waived'
- loan.borrower_type: 'Student', 'Faculty'
- reservation.status: 'Active', 'Fulfilled', 'Expired'
- bookrequest.status: 'Pending', 'Approved', 'Rejected'
- purchaseorder.status: 'Pending', 'Delivered', 'Cancelled'"""


async def _run(question: str) -> dict:
    params = StdioServerParameters(command=sys.executable, args=[MCP_SERVER])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tool_list = await session.list_tools()
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.inputSchema or {
                            "type": "object", "properties": {}, "required": []
                        },
                    },
                }
                for t in tool_list.tools
            ]

            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": question},
            ]
            last_sql = None

            for _ in range(15):
                resp = None
                for p in PROVIDERS:
                    try:
                        resp = await asyncio.wait_for(
                            asyncio.to_thread(
                                p["client"].chat.completions.create,
                                model=p["model"],
                                messages=messages,
                                tools=tools,
                            ),
                            timeout=20,
                        )
                        break
                    except asyncio.TimeoutError:
                        await asyncio.sleep(2)
                        continue
                    except Exception as e:
                        err = str(e).lower()
                        if any(x in err for x in ["429", "rate", "quota", "traffic", "timeout"]):
                            await asyncio.sleep(2)
                            continue
                        raise
                if resp is None:
                    await asyncio.sleep(5)
                    continue
                msg = resp.choices[0].message
                msg_dict = {"role": msg.role, "content": msg.content}
                if msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls
                    ]
                messages.append(msg_dict)

                if not msg.tool_calls:
                    return {"answer": msg.content or "No answer.", "sql": last_sql}

                # Call each tool through MCP protocol
                for call in msg.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments or "{}")

                    if name == "run_query":
                        last_sql = args.get("query")

                    result = await session.call_tool(name, args)
                    output = result.content[0].text if result.content else "{}"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": output,
                    })

    return {"answer": "Could not generate a response.", "sql": last_sql}


def ask(question: str) -> dict:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run(question))
    except BaseException as e:
        # Unwrap ExceptionGroup to find actual error
        if hasattr(e, 'exceptions') and e.exceptions:
            actual = e.exceptions[0]
            # Go deeper if nested
            while hasattr(actual, 'exceptions') and actual.exceptions:
                actual = actual.exceptions[0]
            return {"answer": f"Error: {str(actual)}", "sql": None}
        return {"answer": f"Error: {str(e)}", "sql": None}
    finally:
        loop.close()


TABLE_DESCRIPTIONS = {
    "Department": "Academic departments",
    "Category": "Book categories and genres",
    "Publisher": "Book publishers",
    "Author": "Book authors",
    "Shelf": "Physical library shelves",
    "Book": "Books collection",
    "BookAuthor": "Book–author relationships",
    "Journal": "Academic journals",
    "Student": "Student members",
    "Faculty": "Faculty members",
    "Loan": "Book borrowing records",
    "Reservation": "Book reservations",
    "Fine": "Late-return fines",
    "Supplier": "Book suppliers",
    "PurchaseOrder": "Purchase orders",
    "PurchaseOrderItem": "Purchase order line items",
    "Review": "Book reviews and ratings",
    "Event": "Library events",
    "EventRegistration": "Event registrations",
    "DigitalResource": "Digital / e-resources",
    "DigitalAccess": "Digital resource access logs",
    "BookRequest": "Requested books not in collection",
    "Notification": "User notifications",
}
