"""Module that defines all the tools used by the root agent"""
import math
import datetime
from zoneinfo import ZoneInfo

def get_current_time(country: str) -> dict:
   """Returns the current time in a specified country.
   Args:
       country (str): The name of the country for which to retrieve the current time.
   Returns:
       dict: status and result or error msg.
   """
   if country.lower() == "india":
       tz_identifier = "Asia/Kolkata"
   else:
       return {
           "status": "error",
           "error_message": (
               f"Sorry, I don't have timezone information for {country}."
           ),
       }

   tz = ZoneInfo(tz_identifier)
   now = datetime.datetime.now(tz)
   report = (
       f'The current time in {country} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
   )
   return {"status": "success", "result": report}

ALLOWED_FUNCTIONS = {
   "math": math,
   "exp": math.exp,
   "log": math.log,
   "log10": math.log10,
   "sqrt": math.sqrt,
   "pi": math.pi,
   "e": math.e,
   "ceil": math.ceil,
   "floor": math.floor,
   "round": round,
   "factorial": math.factorial,
   "isinf": math.isinf,
   "isnan": math.isnan,
   "isqrt": math.isqrt,
}

def calculate_expression(expression: str) -> dict:
   """Evaluates a mathematical expression and returns the result.
   Supports basic operators (+, -, *, /, **, %), mathematical functions
   and constants (pi, e). Uses a restricted evaluation context for safe execution.

   Args:
       expression: The mathematical expression to evaluate as a string.
                  Examples: "2 + 2", "sqrt(16) * 2", "log(100, 10)"
   Returns:
       On success: {"result": <calculated value>}
       On error: {"error": <error message>}

   Notes:
       - Use 'x' as the variable (e.g., x**2, not x²)
       - Multiplication must be explicitly indicated with * (e.g., 2*x, not 2x)
       - Powers are represented with ** (e.g., x**2, not x^2)
   """
   try:
       result = eval(
           expression,
           {"__builtins__": {}},
           ALLOWED_FUNCTIONS,
       )
       return {
           "status": "success",
           "result": result
       }
   except Exception as e:
       return {
           "status": "error",
           "error_message": str(e)
       }
