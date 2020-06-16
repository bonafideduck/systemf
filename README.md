[![C/C++ CI](https://github.com/yonhan3/systemf/workflows/C/C++%20CI/badge.svg)](https://github.com/yonhan3/systemf/actions)
| Please Note: Systemf() is 0.9 Beta    |
| ------------------------------------- |
| Systemf() is at the maturity level that it can be tested by interested parties.  See [Future Work](#Future Work) below for more information as to what the MVP for version 1.0 would be. |

# systemf
Prepared statement support for the system command.


## synopsis

    #include <systemf.h>

    int systemf(const char *fmt, ...);

## Example, 

Consider a simple command that takes user input and calls system with it.  Without systemf() you would have to do this:

```
int example_func(char *user_input) {
   char fmt[] = "/bin/mymagicfunc %s";
   char *buf = malloc(sizeof(fmt) + strlen(user_input));
   int result;
   sprintf(buf, fmt, user_input);

   if (buf == NULL) {
       return -1;
   }
   result = system(buf);
   free(buf);
   return result;
}
```
With systemf, all you would have to do is this:
```
int example_func(char *user_input) {
   return systemf1("/bin/mymagicfunc %s", user_input);
}
```

But that isn't the reason systemf() was created (but it is a great advantage).  
There is a big security advantage.  user_input is sent as a single argument and
there is no /bin/sh involved.  So if they did something like, 
`user_input = "goodbye ; rm -rf /"`, the first example would try to execute the 
'rm -rf /' while the second would just send the whole string as a single argument 
to /bin/mymagicfunc.

This doesn't solve everything.  If /bin/mymagicfunc had an injection issue, it might still cause the code to be run, but you can't prevent everything.

## Quict Tour of Through Examples

The easiest way to explain the basics how `systemf1()` works is through a few examples.

**Example 1: Basics**

* `systemf1("/bin/echo The cat%s %d tail%s.", "'', tails, tails == 1 ? "" : "s");`

In the above example, `systemf1()` takes the format input, breaks it into parameters
by the spaces in each command, and sends it to execv.  For example if `tails` 
were 2, it would call execv with these arguments:  
`["/bin/echo", "The", "cat's", "2", "tails."]`.  Also, note that `systemf1()` 
doesn't support `'` in the format string.  This is becuase `systemf1()` supports
no quoting or escaping.

**Example 2: Parameter Splitting**

Now take the following call to `systemf1()` into account:

`systemf1("/bin/echo %s", "this line has spaces");`

`systemf1()` only breaks lines into parameters by spaces and glob expansion. So in the above case, the arguments to execv will be: ["/bin/echo", "this line has spaces"] and it would **not** break the %s into spaces.

**Example 3: File Globbing**

`systemf1()` also supports file globbing in the format string and as a glob paramerter, but not as a string.  Consider these three variations:

1. `systemf1("/bin/echo *.c");`
2. `systemf1("/bin/echo %*p", "*.c");`
3. `systemf1("/bin/echo %s", "*.c");`

The first two will find every `c` file in the current directory and pass those as individual parameters to execv. `["/bin/echo", "a.c", "b.c", "c.c"]`.  While the third will send the text in verbatim: `["/bin/echo", "*.c"]` and since `echo` does not do glob expansion, literally `*.c` will be printed.

There are a caveats to the above.  If the glob pattern matches nothing, the
processing will stop, an error message will be printed, and `-1` will be returned.

Also, note that `systemf1()` supports file path sandboxing.  That is a more advanced
subject than this introducton.  For more information see [File Sandboxing](#file-sandboxing-still-being-designed) below.




## Format String and Argument Parsing

The `fmt` argument to systemf1() specifies the how the code will be called and 
allows a convenient way to bring in parameterized user input.  Think of it as 
limited shell with most of what you would need when calling out to system, but 
protections from the common mistakes when calling system.  The below table
summarizes which characters are allowed in the format string and their meanings.

| Token        | Meaning |
|:------------:| ------- |
| `a-z` `A-Z` ` 0-9` `.` `-` | Nonspecial characters allowed in `fmt`. (0) |
| *space tab*  | *Spaces* and *tabs* are interpreted as parameter separators. |
| `%s`         | Replace this with the string in the next available argument. (5) |
| `%d`         | Replace this with the integer in the next available argument. (5) |
| `%p`         | Like `%s`, but also [file sandboxed](#file-sandboxing-still-being-designed) |
| `%*p`        | Interpret the supplied parameter as a file glob. |
| `%!p`        | Like `%s`, but a trusted parameter for [file sandboxed](#file-sandboxing-still-being-designed) |
| `;`          | Command separator run if previous command exits cleanly. |
| `|`          | Command separator like `;` but also pipes stdout from prev into stdin |
| `&&`         | Command separator run if previous command exits cleanly with zero status. |
| `||`         | Command separator run if previous command exits cleanly with nonzero status. |
| `<`*file*    | Supply the stdin from the specified *file*. (1)(2) |
| `>`*file*    | Redirect the stdout into the specified *file*. (1)(2) |
| `>>`*file*   | Append the stdout into the specified *file*. (1)(3) |
| `2>`*file*   | Redirect the stderr into the specified *file*. (1)(2) |
| `2>>`*file*  | Append the stderr into the specified *file*. (1)(3) |
| `>&2`        | Redirect the stdout into the stderr. (4) |
| `2>&1`       | Redirect stderr into stdout. (4) |
| `&>`*file*   | Redirect stderr and stdout into the specified *file*. (1)(2) |
| `&>>`*file*  | Append stderr and stdout into the specified *file*. (1)(2) |

- (0) All tokens below in the table take precedence during parsing.
- (1) There is an optional space between the redirect and the filename.
- (2) Replace the file if it exists.
- (3) Create the file if it does not exist.
- (4) `systemf1()` currently has no support of swapping the stdout and stderr.
- (5) Currently, no formatting specifiers are supported (like `%5d` or `%-10s`)

## Return Values

The base systemf1() will have the same return values as the system() function.

The following is copied from http://man7.org/linux/man-pages/man3/system.3.html :

*  If any child process could not be created, or its status could not
    be retrieved, the return value is -1 and errno is set to indicate
    the error.

*  If all spawned child processes succeed, then the return value is the
    termination status of the last spawned child process.

## Why is There a "1" in the Systemf1 Name?

The driving force behind developing `systemf` was to have a more secure system.  It seems that as a tool becomes more popular, it gets more security scrutiny.  The developers of `systemf` expect that they will have missed something fundamental that will require a non-backward compatible change to the code.  When that day comes, they will have to choose between breaking code and creating new functions.

By making the systemf versioned in its name, it is more obvious the version that is being run and gives for a more graceful transition.  Perhaps one day, when the implementation is considered rock-solid, the final version can drop the numbering system altogether.  (Any bets how long it will take to detect a new fatal security vulnerability in the design after that step is taken?)

## Future Work

### Required for version 1.0
The following must happen before the 1.0 release.  If not implemented before the 1.0 release, there would be the threat that some capabilities would not be backward compatible.

| Title | Description |
| ----- | ----------- |
| [File Sandboxing](#file-sandboxing) |  A limited sandboxing of file access. |

### Features that will likely be added after verison 1.0.

| Title | Description |
| ----- | ----------- |
| [PATH Support](#path-support) | Currently all executables must include a path.  This will add limited path searching and updating. |
| [Capture Support](#capture-support) | Functions that allow for capturing the standard output and standard error to strings. |
| [STDIN String & File Support](#stdin-string-and-file-support) | Functions that allow for a string or buffers to be suppled for the standard input. |
| [Error Message Redirection](#error-message-redirection) | Redirect stderr messages from `systemf` itself. |

### Features not currently planned.

These features require more discussion and some highly needed use cases to be added.

| Title | Description |
| ----- | ----------- |
| [Background Support](#no-plan-for-background-support) | Running commands in the background. |
| [variables](#no-plan-for-variable-support) | Variable expansion like $HOME or ~ may not be supported. |
| [variable cleaning](#no-plan-for-variable-cleaning) | Other than PATH, no other environment variables will be reset (like IFS). | 

### File Sandboxing
**Still being developed.**

By default, if a file is specified, it must be located in the realpath of the current directory.  We are designing how
this can be expanded and expect alternate paths to be able to be specified in the format string, but that is still being
designed.

### PATH Support
**Still being developed.**

`Systemf` protects against [CWE-426: Untrusted Search Path](https://cwe.mitre.org/data/definitions/426.html) by ignoring the PATH environment variable and trusting a limit path.  For systems that supply it, `confstr(_CS_PATH, ...)` will be used.  For other systems, the `./configure` will need to determine this.

Each executable will have the ability to augment this path for that executable with the command `systemf1_update_path(path, location)` where `path` is a colon separated list of directories and location can be one of `SYSTEMF1_PATH_PREPEND`, `SYSTEMF1_PATH_APPEND`, and `SYSTEMF1_PATH_REPLACE`.  
Systemf by default only allows absolute paths and a very limited PATH parsing.

### Capture Support
**Still being developed.**

`Systemf` will support capturing the standard output to strings.  These strings may either be supplied or allocated.  There are two base commands for this:

```
systemf1_capture_rtn systemf1_capture(
    char *stdout_buf, 
    size_t max_stdout_buf_len, 
    char *stderr_buf, 
    size_t max_stderr_buf_len, 
    fmt, 
    ...);
    
systemf1_capture_rtn *systemf1_capture_a(
    size_t max_stdout_buf_len, 
    size_t max_stderr_buf_len, 
    fmt, 
    ...);
```

`systemf1_capture_rtn` contains information about the captured results.  For the former, it will be passed back by value and the latter, it will be allocated and returned.  A single `free()` of the latter will be required because the captured data will be opaquely appended to the structure.  The structure will contain the following fields:

| Field | Description |
| ----- | ----------- |
| stdout | A buffer pointer containing the standard output.  `out_buf[out_buf_len] will always contain the nul terminator. |
| stdout_len | The number of characters written to out_buf excluding the nul terminator.  This will never be greater than max_out_buf_len - 1 |
| stdout_total | The number of total bytes received from the stdout if `max_stdout_buf_len` were infinite. |
| stderr  | Similar to `stdout` but for stderr |
| stderr_len | Similar to `stdout_len` but for `stderr` |
| stderr_total | Similar to `stdout_total` but for `stderr` |
| retval | The same return value as `systemf1()` would normally return. |

There are some corner cases for `systemf1_capture()`.
* If `stdout_buf` is NULL, `max_stdout_buf_len` will be ignored.  The returned stdout will be NULL and `stdout_len` will be zero, but `stdout_total` will be accurate.
* If `max_stdout_buf_len` is 0, the code will act as if `stdout_buf` were NULL.
* The same corner cases exist for `stderr_buf` and `max_stderr_buf_len`.

There are some corner cases for `systemf1_capture_a()`.
* A `max_stdout_buf_len` of 0 considered to be equivalent to a length of 1.  A one byte buffer will be allocated and returned filled with a nul value.  Infinite buffer size is not supported.
* The same corner cases exist for `max_stderr_buf_len`.

### Stdin String and File Support

Varients of the systemf1 suite will take either a string, a buffer, or a FILE pointer and use that as the standard input.  These variants will take one of the above as their first argument and in the case of the buffer, a length argument.
This will create a wide varienty of new functions:

```
systemf1_sin(char *string, ...);
systemf1_bin(char *buf, buflen,...);
systemf1_fin(FILE *file, ...);

systemf1_sin_capture(char *string, ...);
systemf1_bin_capture(char *buf, buflen, ...);
systemf1_fin_capture1(FILE *file, ...);

systemf1_sin_capture_a(char *string, ...);
systemf1_bin_capture_a(char *buf, buflen, ...);
systemf1_fin_capture_a(FILE *file, ...);
```

### Error Message Redirection

`systemf` will print error messages to the standard error in some situations.  These include invalid format strings, sandboxing violations, commands not found, and file globbing problems. Global setting command `systemf1_log_to(FILE *file)` will be added.  It will return the current log.  Supplying `file=NULL` completely disables logging.  This does not affect the normal stderr and stdout processing of the commands themselves.

### No Plan for Background Support

The standard shell contains facilities to run commands in the background with the
`&` parameter.  The main reason this is not currently planned is that a much better understanding of how the shell handles the processing in needed.  This support is likely to be the most requested of all the current "No Plan" items.

### No Plan for Variable Support

`Systemf` does not support variable expansion in the format string.  Thus, 
`systemf1("/bin/echo $HOME")` will cause a parse error because `$` is not supported
in the format string.  There were two reasons not to support this.  The first was
that it simple added complexity to the system when the developers were uncertain
how needed such a capability was.  The second was that if such a capability is
added, all security ramification should be considered and discussed first.

For now, there is no variable support.  In the future, there may be.


### No Plan for Variable Cleaning

The SEI CERT C Coding Standard includes [ENV03-C Sanitize the environment when invoking external programs](https://wiki.sei.cmu.edu/confluence/display/c/ENV03-C.+Sanitize+the+environment+when+invoking+external+programs) and its examples include such items as resetting environment variables such as the PATH.  Because it is such a common vulnerability, `Systemf` does sanitize the PATH.  But because the library isn't able to guess every variation of needs of environment variables, it does not sanitize other variables.

## Building

To build, run `./configure && make build`.

If you are a developer of `systemf`, see the [developer instructions](DEVELOP.md).

## Issues and feature requests.

Systemf is currently in a [temporary location](https://github.com/yonhan3/systemf). 
Issues may be raised [there](https://github.com/yonhan3/systemf/issues), but may 
not get transferred to its [permanant home](https://github.com/cisco/systemf).
