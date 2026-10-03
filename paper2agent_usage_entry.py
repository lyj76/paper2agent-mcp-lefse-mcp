import runpy,sys
from pathlib import Path
from fastmcp import FastMCP
from paper2agent_usage import attach_usage
ROOT=Path(__file__).resolve().parent
ENTRY=ROOT/'server.py'
sys.path[:0]=[str(ENTRY.parent),str(ROOT)]
namespace=runpy.run_path(str(ENTRY),run_name='paper2agent_usage_server')
server=next(x for x in namespace.values() if isinstance(x,FastMCP))
attach_usage(server,ROOT/'mcp-usage.json')
if __name__=='__main__':server.run()
