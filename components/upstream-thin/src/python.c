/* POSIX-equivalent of CPython 3.14 Programs/python.c. */
#include <Python.h>
int main(int argc, char **argv) { return Py_BytesMain(argc, argv); }
