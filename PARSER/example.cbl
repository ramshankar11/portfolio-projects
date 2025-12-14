       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTPROC.
      *
      * Sample Enterprise COBOL program for processing customer records.
      *
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-INPUT  ASSIGN TO CUSTIN
                                  ORGANIZATION IS SEQUENTIAL
                                  ACCESS MODE IS SEQUENTIAL
                                  FILE STATUS IS WS-CUSTIN-STATUS.
           SELECT CUSTOMER-OUTPUT ASSIGN TO CUSTOUT
                                  ORGANIZATION IS SEQUENTIAL
                                  ACCESS MODE IS SEQUENTIAL
                                  FILE STATUS IS WS-CUSTOUT-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-INPUT RECORD CONTAINS 80 CHARACTERS.
       01  INPUT-RECORD-LAYOUT     PIC X(80).
      
       FD  CUSTOMER-OUTPUT RECORD CONTAINS 80 CHARACTERS.
       01  OUTPUT-RECORD-LAYOUT    PIC X(80).

       WORKING-STORAGE SECTION.

      * Include common data definitions (Copybooks)
       COPY CUSTDATL.                *> Defines 01 CUST-REC-LAYOUT
       COPY FILESTAT.                *> Defines file status codes

      * Working storage variables
       01  WS-CUSTIN-STATUS        PIC 99 VALUE ZEROS.
       01  WS-CUSTOUT-STATUS       PIC 99 VALUE ZEROS.
       01  WS-EOF-SW               PIC X(1) VALUE 'N'.
           88  EOF-REACHED         VALUE 'Y'.
           88  NOT-EOF             VALUE 'N'.

       PROCEDURE DIVISION.
       MAIN-PROCESSING SECTION.
           PERFORM 1000-INITIALIZE
           PERFORM 2000-PROCESS-RECORDS UNTIL EOF-REACHED
           PERFORM 3000-TERMINATE
           STOP RUN.

       1000-INITIALIZE.
           OPEN INPUT CUSTOMER-INPUT
                OUTPUT CUSTOMER-OUTPUT
           IF WS-CUSTIN-STATUS NOT = FS-OK
               DISPLAY 'ERROR: Failed to open input file, Status: ' 
                       WS-CUSTIN-STATUS
               MOVE 'Y' TO WS-EOF-SW
           END-IF
           READ CUSTOMER-INPUT INTO CUST-REC-LAYOUT
           AT END 
               MOVE 'Y' TO WS-EOF-SW
           END-READ.

       2000-PROCESS-RECORDS.
           * Business logic goes here (e.g., validate, calculate, format)
           * This example just moves the data
           MOVE CUST-REC-LAYOUT TO OUTPUT-RECORD-LAYOUT
           WRITE OUTPUT-RECORD-LAYOUT
           READ CUSTOMER-INPUT INTO CUST-REC-LAYOUT
           AT END
               MOVE 'Y' TO WS-EOF-SW
           END-READ.

       3000-TERMINATE.
           CLOSE CUSTOMER-INPUT
                 CUSTOMER-OUTPUT.

       END PROGRAM CUSTPROC.
