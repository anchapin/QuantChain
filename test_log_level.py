
Let me create a simple test file to understand the issue better:
<tool_call>create_file
<arg_key>path</arg_key>
<arg_value>QuantChain/test_log_level.py</arg_value>
<arg_key>mode</arg_key>
<arg_value>create</arg_value>
<arg_key>display_description</arg_key>
<arg_value>Create test file to check log_level behavior</arg_value>
<arg_key>content</arg_key>
<arg_value>from quantchain.core.config import QuantChainConfig, LogLevel

config = QuantChainConfig(log_level=LogLevel.DEBUG)
print("log_level attribute:", config.log_level)
print("isinstance of LogLevel:", isinstance(config.log_level, LogLevel))
print("dir of config:", [x for x in dir(config) if not x.startswith('_')])

config_dict = config.to_dict()
print("config_dict keys:", list(config_dict.keys()))</arg_value>
</tool_call>
