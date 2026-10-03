"""Data-only MCP usage metadata. Never changes arguments, defaults or tool execution."""
import copy
import json
from pathlib import Path


def attach_usage(server, path):
    path = Path(path)
    if path.stat().st_size > 128 * 1024:
        raise ValueError('MCP usage metadata exceeds budget')
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schemaVersion') != 1:
        raise ValueError('unsupported MCP usage metadata')
    tools = data.get('tools', {})
    if not isinstance(tools, dict) or len(tools) > 100:
        raise ValueError('invalid usage tool metadata')
    from fastmcp.server.transforms import Transform

    class UsageDescriptions(Transform):
        def revise(self, tool):
            guidance = tools.get(tool.name)
            if not guidance:
                return tool
            parameters = copy.deepcopy(tool.parameters)
            for name, description in guidance.get('parameters', {}).items():
                if name not in parameters.get('properties', {}):
                    raise ValueError('usage metadata names unknown parameter: ' + tool.name + '.' + name)
                parameters['properties'][name]['description'] = str(description)
            return tool.model_copy(update={'description': str(guidance['description']), 'parameters': parameters})

        async def list_tools(self, values):
            return [self.revise(tool) for tool in values]

        async def get_tool(self, name, call_next, *, version=None):
            tool = await call_next(name, version=version)
            return self.revise(tool) if tool else None

    server.add_transform(UsageDescriptions())
    for uri, item in data.get('resources', {}).items():
        # Function defaults must not become resource URI parameters.
        def resource_factory(body):
            def read() -> str:
                return body
            return read
        try:
            server.local_provider.remove_resource(uri)
        except KeyError:
            pass
        server.resource(uri, name=item.get('name', uri), mime_type='text/plain')(resource_factory(item['text']))
    for name, item in data.get('prompts', {}).items():
        def prompt_factory(body):
            def prompt() -> str:
                return body
            return prompt
        try:
            server.local_provider.remove_prompt(name)
        except KeyError:
            pass
        server.prompt(name=name, description=item.get('description', 'MCP 使用指导'))(prompt_factory(item['text']))
    return data
