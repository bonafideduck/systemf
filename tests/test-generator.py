import sys
import os
from typing import Any
import string
import json

template = """
/*
 * DO NOT EDIT THIS FILE.
 * This files was generated by test-generator.py.
 * Any changes should be done there.
 * DO NOT EDIT THIS FILE.
 */

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "../src/systemf.h"

static void sigsegv_handler(int signo) {{
    fputs("Test aborted due to a SEGV\\n", stderr);
    exit(EXIT_FAILURE);
}}

static void sanity_check_tests_dir(void) {{
    const size_t bufsize = 4096;
    char *buf = malloc(bufsize);
    if (!buf) {{
        fprintf(stderr, "Test aborted because %zu bytes were not available.\\n", bufsize);
        exit(EXIT_FAILURE);
    }}

    char *cwd = getcwd(buf, bufsize);
    if (!cwd) {{
        fputs("Test aborted because current working directory could not be extracted\\n", stderr);
        exit(EXIT_FAILURE);
    }}

    char *tests = NULL;
    for (char *s = strstr(cwd, "tests"); s; s = strstr(s+5, "tests")) {{
        tests = s;
    }}
    if (!tests || (tests - cwd) < (strlen(cwd) - 6)) {{
        fputs("This command must be run in the tests directory.\\n", stderr);
        exit(EXIT_FAILURE);
    }}
}}

{test_funcs}

{test_funcs_table}

static void usage() {{
    puts("usage: test-runner <testnum>");
    puts("");
    puts("testnum: Test Description");
{usage_tests}
}}

int main(int argc, const char *argv[]) {{
    int index = 0;
    if (argc == 2) {{
        index = atoi(argv[1]);
    }}

    if (index == 0 || index > {max_tests}) {{
        usage();
        exit(EXIT_FAILURE);
    }}

    sanity_check_tests_dir();

    // Set above function as signal handler for the SIGINT signal:
    if (signal(SIGSEGV, sigsegv_handler) == SIG_ERR) {{
        fputs("An error occurred while setting a signal handler.\\n", stderr);
        return EXIT_FAILURE;
    }}

    return test_func_table[index - 1]();
}}
"""

def eprint(s: str):
    print(s, file=sys.stderr)

def str2func(index: int, s: str) -> str:
    """Creates a unique c-function name from a string.
    Credit: https://stackoverflow.com/questions/34544784/arbitrary-string-to-valid-python-name
    """
    VALID_NAME_CHARACTERS = string.ascii_letters + string.digits
    PLACEHOLDER = "_"
    prefix = f"test_{index + 1}_"
    sym = ''.join(c.lower() if c in VALID_NAME_CHARACTERS else PLACEHOLDER for c in s)
    return prefix + sym

def cstr_escape(s: str) -> str:
    return s.replace("\"", "\\\"")

test_func_template = """
static int {test_name}() {{
    return systemf1({test_args});
}}
"""

def generate_test_func(index: int, test: dict) -> str:
    command = test['command']
    test_name = str2func(index, test['description'])
    test_args = []

    for arg in command:
        if type(arg) is str:
            # Replace ['#'] arguments with the string representation of this test number.
            arg = arg.replace("#", str(index+1))
            test_args.append(f'"{cstr_escape(arg)}"')
        elif type(arg) is int:
            test_args.append(f'{arg}')
        else:
            eprint(f'# Unknown arg type, aborting: {arg}')
            sys.exit(1)
    test_args = ", ".join(test_args)
    return test_func_template.format(test_name=test_name, test_args=test_args)

def generate_test_funcs(tests: list) -> str:
    return "".join([generate_test_func(i, f) for i, f in enumerate(tests)])

def generate_usage_tests(tests: list) -> str:
    result = ""
    for index, test in enumerate(tests):
        line = f"{index + 1:7}: {test['description']}"
        result += f'    puts("{cstr_escape(line)}");\n'
    return result

test_func_table_template = """
int (*(test_func_table[]))(void) = {{
{test_functions}
}};
"""

def generate_test_func_table(tests: list) -> str:
    test_functions = "\n".join([f'    {str2func(i, t["description"])},' for i, t in enumerate(tests)])
    return(test_func_table_template.format(test_functions=test_functions))

def generate_kwargs(tests: list) -> str:
    kwargs = {}
    kwargs["usage_tests"] = generate_usage_tests(tests)
    kwargs["test_funcs"] = generate_test_funcs(tests)
    kwargs["test_funcs_table"] = generate_test_func_table(tests)
    kwargs["max_tests"] = len(tests)
    return kwargs

def get_tests() -> list:
    current_dir = os.path.dirname(sys.argv[0])
    TEST_JSON = os.path.join(current_dir, 'test.json')
    with open(TEST_JSON, 'r') as json_file:
        try:
            return json.load(json_file)
        except Exception as e:
            eprint(f'# Error loading json: {str(e)}')
            sys.exit(-1)

def main() -> int:
    tests = get_tests()
    kwargs = generate_kwargs(tests)

    with open("tests/test-runner.c", "w") as t:
        t.write(template.format(**kwargs))
    return 0

sys.exit(main())