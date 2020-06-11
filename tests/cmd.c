/*
 * cmd - Used by the test harness to have a consistent
 * test command with no reliance on any external files.
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    int retval = 0;

    if (argc == 1) {
        printf("%s", 
            "stdout: echo '1' to the stdout with no linefeed.\n"
            "stderr: echo '2' to the stderr with no linefeed.\n"
            "{}:     wrap the stdin with {}\n"
            "incr:   read the first intter from the stdin, add 1, and print to stdout.\n" 
            "comma:  read the rest of the arguments and print to the stdout comma separated.\n"
            "false:  set the return value to 1 (0 is the default).\n"
            "return: set the return value to the next argument\n");
        return retval;
    } 

    for (int argi = 1; argi < argc; argi++) {
        if (!strcmp("stdout", argv[argi])) {
            printf("1");
        } else if (!strcmp("stderr", argv[argi])) {
            fprintf(stderr, "2");
        } else if (!strcmp("{}", argv[argi])) {
            printf("{");
            char buf[257];
            while (1) {
                int count = read(0, buf, 256);
                if (count < 1) {
                    break;
                }
                buf[count] = 0;
                printf("%s", buf);
            }
            printf("}");
        } else if (!strcmp("incr", argv[argi])) {
            int i;
            fscanf(stdin, "%d", &i);
            i = i + 1;
            printf("%d", i);
        } else if (!strcmp("comma", argv[argi])) {
            char *delim="";
            for (argi++; argi < argc; argi++) {
                printf("%s%s", delim, argv[argi]);
                delim = ",";
            }
        } else if (!strcmp("false", argv[argi]))  {
            retval = 1;
        } else if (!strcmp("return", argv[argi]))  {
            argi++;
            if (argi < argc) {
                retval = atoi(argv[argi]);
            }
        } else {
            printf("\nInvalid option %s\n", argv[argi]);
        }
    }
    return retval;
}
