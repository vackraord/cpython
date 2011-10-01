/* this is sort of a hack.  there's at least one place (formatting
   floats) where some stringlib code takes a different path if it's
   compiled as unicode. */
#define STRINGLIB_IS_UNICODE     1

#define FASTSEARCH               ucs1lib_fastsearch
#define STRINGLIB(F)             ucs1lib_##F
#define STRINGLIB_OBJECT         PyUnicodeObject
#define STRINGLIB_CHAR           Py_UCS1
#define STRINGLIB_TYPE_NAME      "unicode"
#define STRINGLIB_PARSE_CODE     "U"
#define STRINGLIB_EMPTY          unicode_empty
#define STRINGLIB_ISSPACE        Py_UNICODE_ISSPACE
#define STRINGLIB_ISLINEBREAK    BLOOM_LINEBREAK
#define STRINGLIB_ISDECIMAL      Py_UNICODE_ISDECIMAL
#define STRINGLIB_TODECIMAL      Py_UNICODE_TODECIMAL
#define STRINGLIB_TOUPPER        Py_UNICODE_TOUPPER
#define STRINGLIB_TOLOWER        Py_UNICODE_TOLOWER
#define STRINGLIB_FILL           Py_UNICODE_FILL
#define STRINGLIB_STR            PyUnicode_1BYTE_DATA
#define STRINGLIB_LEN            PyUnicode_GET_LENGTH
#define STRINGLIB_NEW            _PyUnicode_FromUCS1
#define STRINGLIB_RESIZE         not_supported
#define STRINGLIB_CHECK          PyUnicode_Check
#define STRINGLIB_CHECK_EXACT    PyUnicode_CheckExact
#define STRINGLIB_GROUPING       _PyUnicode_InsertThousandsGrouping
#define STRINGLIB_GROUPING_LOCALE _PyUnicode_InsertThousandsGroupingLocale

#define STRINGLIB_TOSTR          PyObject_Str
#define STRINGLIB_TOASCII        PyObject_ASCII

#define _Py_InsertThousandsGrouping _PyUnicode_ucs1_InsertThousandsGrouping
#define _Py_InsertThousandsGroupingLocale _PyUnicode_ucs1_InsertThousandsGroupingLocale

