import re
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

description = "This addon allows you to execute a python code in a new InteractiveShell. Include prints or returns to get the output."

parameters = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "The python code to be executed in an InteractiveShell, include prints or returns to get the output, This is a temporary terminal, so you can't use input() or anything that requires user input.",
        },
        "start_new_terminal": {
            "type": "boolean",
            "default": False,
            "description": "Start a new terminal for this execution? If True, all previous variables will be lost, only start a new terminal if absolutely necessary or asked explicitly.",
        }
    },
    "required": ['content', 'start_new_terminal'],
}

shell = InteractiveShell.instance()

preload_content = """
# add a way to preload content here
"""

shell.run_cell(preload_content)

def run_python_code(content, start_new_terminal):
    try:
        global shell
        if start_new_terminal:
            shell = InteractiveShell.instance()

        with capture_output() as captured:
            output = shell.run_cell(content)

        # remove color codes from standard output and standard error
        captured_stdout = re.sub(r'\x1b\[[0-9;]*m', '', captured.stdout)
        captured_stderr = re.sub(r'\x1b\[[0-9;]*m', '', captured.stderr)

        # Check if there's a result from the executed code
        result = output.result if output.result is not None else ""

        def safe_slice(obj, length=450):
            if not isinstance(obj, (str, list)):
                obj = str(obj)
            return obj[:length]
        
        # Prepare the response
        response = {
            'output': safe_slice(result), 
            'stdout': safe_slice(captured_stdout), 
            'stderr': safe_slice(captured_stderr), 
            'error': output.error_in_exec
        }

        return response

    except Exception as e:
        return {'error': str(e)}