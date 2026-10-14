# Data transcribed from the paper

Source: arXiv:2012.01198v4, Table III, rows 30-75 (PDFBox). The values are copied by hand, and
`analysis/check_paper_table3.py` checks them against the totals printed in the table.

`table3_pdfbox.csv` holds the absolute counts only. The percentages printed in the paper are recomputed by the
scripts instead of copied, because some of them are off by a factor of 100 (for example `1 / 18 (0.05%)`).

Corrections:
- The row for `PDCIDFontType2_codeToGID` is printed with number 59, which is also used for
  `PDExtendedGraphicsState_getNonStrokingOverprintControl`. Its position in the table is row 49, and that is the
  number used here.
- Row 67 (`PDICCBased_getDefaultDecode`) prints `8 / 18 (44.4%)` for #UNIQUE while #COLLECTED is 16. The CSV keeps
  #COLLECTED = 16 and #UNIQUE = 8.

Totals printed in the paper (row PDFBOX_TOTAL), used as the reference by the check script:

| invocations | collected | unique | tests | passing | failing | well-tested | pseudo-tested |
|---|---|---|---|---|---|---|---|
| 121,175 | 57,563 | 13,851 | 13,851 | 13,614 | 237 | 28 | 18 |
