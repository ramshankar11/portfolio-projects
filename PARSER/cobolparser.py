import re
import json
import sys
import os
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

class SourceFormat(Enum):
    FIXED = "FIXED"
    FREE = "FREE"

class Token:
    def __init__(self, type_: str, value: str, line_num: int):
        self.type = type_
        self.value = value
        self.line_num = line_num
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"

class CobolParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.raw_lines: List[str] = []
        self.source_format: SourceFormat = SourceFormat.FIXED
        self.parsed_data: Dict[str, Any] = {
            "metadata": {
                "file": os.path.basename(filepath),
                "format": "UNKNOWN"
            },
            "identification_division": {},
            "environment_division": {},
            "data_division": [],
            "procedure_division": {} 
        }

    def load_file(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
                self.raw_lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: File not found: {self.filepath}")
            sys.exit(1)

    def detect_format(self):
        check_lines = [l for l in self.raw_lines if l.strip()][:20]
        if not check_lines:
            self.source_format = SourceFormat.FIXED
            return

        fixed_indicators = 0
        total_checked = 0

        for line in check_lines:
            if len(line) > 6:
                seq_area = line[0:6]
                indicator = line[6]
                if indicator in ['*', '/', '-', ' ', 'D']:
                    if seq_area.isdigit() or seq_area.strip() == "":
                        fixed_indicators += 1
            total_checked += 1

        if total_checked > 0 and (fixed_indicators / total_checked) >= 0.8:
            self.source_format = SourceFormat.FIXED
        else:
            self.source_format = SourceFormat.FREE
        
        self.parsed_data["metadata"]["format"] = self.source_format.value

    def clean_lines(self) -> List[Tuple[int, str]]:
        cleaned = []
        for idx, line in enumerate(self.raw_lines):
            line_num = idx + 1
            line_val = line.rstrip('\n')
            
            if self.source_format == SourceFormat.FIXED:
                if len(line_val) < 7: continue
                indicator = line_val[6]
                if indicator in ['*', '/']: continue 
                content = line_val[7:72]
                if content.strip() == "": continue
                cleaned.append((line_num, content))
                
            else:
                if "*>" in line_val:
                    content = line_val.split("*>")[0]
                else:
                    content = line_val
                if content.strip() == "": continue
                cleaned.append((line_num, content))
        
        return cleaned

    def _parse_data_entry(self, line: str) -> Optional[Dict[str, Any]]:
        clean = line.rstrip('.')
        parts = clean.split()
        if not parts: return None
        level = parts[0]
        if not level.isdigit(): return None
        
        entry = {
            "level": level,
            "name": "",
            "picture": None,
            "usage": None,
            "value": None
        }
        
        if len(parts) > 1:
            entry["name"] = parts[1]
        
        rest_of_line = " ".join(parts[2:])
        pic_match = re.search(r'\b(PIC|PICTURE)\s+(IS\s+)?([A-Z0-9\(\)V9S]+)', rest_of_line, re.IGNORECASE)
        if pic_match:
            entry["picture"] = pic_match.group(3)
        val_match = re.search(r'\bVALUE\s+(IS\s+)?(.+)', rest_of_line, re.IGNORECASE)
        if val_match:
            raw_val = val_match.group(2)
            entry["value"] = raw_val.strip()
        usage_match = re.search(r'\b(COMP|COMP-3|BINARY|DISPLAY|PACKED-DECIMAL)\b', rest_of_line, re.IGNORECASE)
        if usage_match:
            entry["usage"] = usage_match.group(1)

        return entry

    def parse(self):
        self.load_file()
        self.detect_format()
        lines = self.clean_lines()
        
        current_division = None
        current_section = None
        
        procedure_lines = []
        
        div_pattern = re.compile(r'^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\s*\.?', re.IGNORECASE)
        sec_pattern = re.compile(r'^\s*([\w-]+)\s+SECTION\s*\.?', re.IGNORECASE)

        for line_num, line_content in lines:
            line_stripped = line_content.strip()

            div_match = div_pattern.match(line_stripped)
            if div_match:
                current_division = div_match.group(1).upper() + " DIVISION"
                current_section = None
                continue

            sec_match = sec_pattern.match(line_stripped)
            if sec_match:
                current_section = sec_match.group(1).upper()
                if current_division == "PROCEDURE DIVISION":
                     procedure_lines.append((line_num, line_content))
                continue
            
            if current_division == "IDENTIFICATION DIVISION":
                parts = line_stripped.split('.', 1)
                if len(parts) > 0:
                    key = parts[0].strip()
                    val = parts[1].strip().rstrip('.') if len(parts) > 1 else ""
                    if key and val:
                        self.parsed_data["identification_division"][key] = val
            
            elif current_division == "ENVIRONMENT DIVISION":
                if current_section:
                    if current_section not in self.parsed_data["environment_division"]:
                        self.parsed_data["environment_division"][current_section] = []
                    self.parsed_data["environment_division"][current_section].append(line_stripped)
            
            elif current_division == "DATA DIVISION":
                if "SECTION" in line_stripped and sec_match: continue
                entry = self._parse_data_entry(line_stripped)
                if entry:
                    entry["section"] = current_section
                    self.parsed_data["data_division"].append(entry)

            elif current_division == "PROCEDURE DIVISION":
                procedure_lines.append((line_num, line_content))

        if procedure_lines:
            proc_parser = ProcedureParser(procedure_lines)
            self.parsed_data["procedure_division"] = proc_parser.parse()


class ProcedureParser:
    def __init__(self, lines: List[Tuple[int, str]]):
        self.lines = lines
        self.tokens: List[Token] = []
        self.pos = 0
        self.length = 0

    def tokenize(self):
        token_pattern = re.compile(r"""('[^']*'|"[^"]*"|[\w-]+|.)""")
        for line_num, text in self.lines:
            matches = token_pattern.findall(text)
            for m in matches:
                val = m.strip()
                if not val: continue
                self.tokens.append(Token("WORD", val, line_num))
        self.length = len(self.tokens)

    def parse(self) -> Dict[str, Any]:
        self.tokenize()
        structure = {}
        current_paragraph = "_ROOT_"
        structure[current_paragraph] = []
        
        while self.pos < self.length:
            token = self.peek()
            
            if self.is_paragraph_start():
                para_name = self.consume().value
                if self.peek() and self.peek().value == '.':
                   self.consume() # eat dot
                current_paragraph = para_name
                structure[current_paragraph] = []
                continue
            
            start_pos = self.pos
            stmt = self.parse_statement()
            if stmt:
                structure[current_paragraph].append(stmt)
            else:
                # Only consume if we didn't advance (e.g. unmatched terminator)
                if self.pos == start_pos:
                    if self.pos < self.length:
                        self.consume()
                
        return structure

    def is_paragraph_start(self) -> bool:
        t1 = self.peek(0)
        t2 = self.peek(1)
        if t1 and t2 and t2.value == '.' and t1.type == "WORD":
            reserved = {
                "EXIT", "GOBACK", "STOP", "RUN", "END-IF", "END-PERFORM", "END-EVALUATE", 
                "END-READ", "END-CALL", "END-STRING", "END-UNSTRING", "ELSE"
            }
            if t1.value.upper() not in reserved:
                return True
        return False

    def parse_statement(self) -> Optional[Dict[str, Any]]:
        token = self.peek()
        if not token: return None
        if token.value == '.': 
            self.consume()
            return None 

        verb = token.value.upper()
        if verb == "IF":
            return self.parse_if()
        elif verb == "EVALUATE":
            return self.parse_evaluate()
        elif verb == "PERFORM":
            return self.parse_perform()
        elif verb == "CALL":
            return self.parse_call()
        elif verb == "MOVE":
            return self.parse_move()
        elif verb == "GO": 
            return self.parse_go_to()
        elif verb in ["END-IF", "END-EVALUATE", "END-PERFORM", "ELSE", "WHEN"]:
            return None 
        else:
            return self.parse_generic()

    def parse_block(self, terminators: set) -> List[Dict[str, Any]]:
        statements = []
        while self.pos < self.length:
            token = self.peek()
            if not token: break
            
            if token.value.upper() in terminators:
                break

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            else:
                 # Check again after trying to parse
                 curr = self.peek()
                 if curr and curr.value.upper() in terminators:
                     break
                 
                 if self.pos > 0 and self.tokens[self.pos-1].value == '.':
                     break
                 
                 # Break on unconsumed junk or unmatched terminator
                 break
        return statements

    def parse_if(self):
        self.consume() # IF
        
        condition_tokens = []
        while self.pos < self.length:
            t = self.peek()
            if t.value.upper() == "THEN":
                self.consume()
                break
            if t.value == '.': break 
            
            verbs = {"MOVE", "DISPLAY", "PERFORM", "IF", "GO", "CALL", "ADD", "SUBTRACT", "COMPUTE", "SET", "EVALUATE", "NEXT"}
            if t.value.upper() in verbs and t.value.upper() not in ["IS", "NOT", "OR", "AND", "GREATER", "LESS", "EQUAL", "THAN"]:
                 break
                 
            condition_tokens.append(self.consume().value)

        condition_str = " ".join(condition_tokens)
        then_stmts = self.parse_block({"ELSE", "END-IF", "."})
        
        else_stmts = []
        if self.peek() and self.peek().value.upper() == "ELSE":
            self.consume()
            else_stmts = self.parse_block({"END-IF", "."})
            
        if self.peek() and self.peek().value.upper() == "END-IF":
            self.consume()
            
        return {
            "type": "IF",
            "condition": condition_str,
            "then": then_stmts,
            "else": else_stmts
        }

    def parse_evaluate(self):
        self.consume() # EVALUATE
        subject_tokens = []
        while self.pos < self.length:
            t = self.peek()
            if t.value.upper() == "WHEN": break
            if t.value == '.': break
            subject_tokens.append(self.consume().value)
        
        subject = " ".join(subject_tokens)
        cases = []
        
        while self.peek() and self.peek().value.upper() == "WHEN":
            self.consume() 
            when_cond = []
            while self.pos < self.length:
                t = self.peek()
                verbs = {"MOVE", "DISPLAY", "PERFORM", "IF", "GO", "CALL", "ADD", "SUBTRACT", "SET", "CONTINUE"}
                if t.value.upper() in verbs or t.value.upper() in ["WHEN", "END-EVALUATE"]:
                     break
                if t.value == '.': break
                when_cond.append(self.consume().value)
            cond_str = " ".join(when_cond)
            body = self.parse_block({"WHEN", "END-EVALUATE", "."})
            cases.append({"condition": cond_str, "statements": body})
            
        if self.peek() and self.peek().value.upper() == "END-EVALUATE":
            self.consume()
            
        return {"type": "EVALUATE", "subject": subject, "cases": cases}

    def parse_perform(self):
        self.consume() 
        details = []
        is_inline = False
        has_procedure = False
        
        while self.pos < self.length:
            t = self.peek()
            
            # Check first token to determine if it's potentially out-of-line (has procedure name)
            if not details and t.value.upper() not in ["END-PERFORM", ".", "VARYING", "UNTIL", "TIMES", "WITH", "TEST"]:
                 has_procedure = True

            if t.value.upper() == "END-PERFORM":
                is_inline = True
                break
            
            # If we hit a verb:
            if t.value.upper() in ["MOVE", "IF", "DISPLAY", "CALL", "SET", "ADD", "SUBTRACT", "GO", "EVALUATE", "CONTINUE", "STOP", "EXIT", "READ", "WRITE"]: 
                if has_procedure:
                    # e.g. PERFORM PARA ... IF ...
                    # The IF is the next statement, not body.
                    break
                else:
                    # PERFORM UNTIL ... IF ...
                    # The IF is start of body.
                    is_inline = True
                    break
            
            if t.value == '.': break
            details.append(self.consume().value)
            
        body = []
        # If explicitly inline (hit Verb without Procedure, or hit END-PERFORM), parse body
        # Note: If we broke on Verb with has_procedure=False, is_inline is True.
        # If we broke on Verb with has_procedure=True, is_inline is False.
        # If we broke on END-PERFORM, is_inline is True.
        
        if is_inline:
             # If we broke on END-PERFORM, body might be empty? or we consumed everything into details?
             # No, if END-PERFORM, body is between details and END-PERFORM. 
             # Wait, my loop consumes into details until break.
             # If END-PERFORM, we broke. details has the header. Body is empty? 
             # No, inline perform has statements.
             # "PERFORM ... statements ... END-PERFORM"
             # My loop would consume "statements" into "details" if they are not Verbs?
             # But statements start with Verbs.
             # So loop breaks on first Verb.
             # Then we call parse_block.
             body = self.parse_block({"END-PERFORM", "."})
        
        if self.peek() and self.peek().value.upper() == "END-PERFORM":
            self.consume()
        
        return {"type": "PERFORM", "details": " ".join(details), "body": body}

    def parse_call(self):
        self.consume() 
        target = self.consume().value
        args = []
        while self.pos < self.length:
            t = self.peek()
            if t.value == '.': break
            if t.value.upper() in ["END-CALL"]: break
            if t.value.upper() in ["ON", "EXCEPTION"]: break
            args.append(self.consume().value)
        if self.peek() and self.peek().value.upper() == "END-CALL":
            self.consume()
        return {"type": "CALL", "target": target, "arguments": " ".join(args)}
    
    def parse_move(self):
        self.consume()
        tokens = []
        while self.pos < self.length:
            t = self.peek()
            if t.value == '.': break
            verbs = {"MOVE", "IF", "PERFORM", "CALL"} 
            if t.value.upper() in verbs: break
            tokens.append(self.consume().value)
        return {"type": "MOVE", "statement": "MOVE " + " ".join(tokens)}

    def parse_go_to(self):
        self.consume()
        if self.peek() and self.peek().value.upper() == "TO":
            self.consume()
        target = self.consume().value
        return {"type": "GO TO", "target": target}

    def parse_generic(self):
        tokens = []
        first = self.consume().value
        tokens.append(first)
        while self.pos < self.length:
            t = self.peek()
            if t.value == '.': break
            if t.value.upper() in ["ELSE", "END-IF", "WHEN", "END-EVALUATE", "END-PERFORM", "END-CALL"]:
                break
            verbs = {"MOVE", "DISPLAY", "PERFORM", "IF", "GO", "CALL", "ADD", "SUBTRACT", "COMPUTE", "SET", "EVALUATE", "CONTINUE", "RETURN", "OPEN", "CLOSE", "READ", "WRITE", "REWRITE", "DELETE", "START", "STOP", "EXIT"}
            if t.value.upper() in verbs:
                break
            tokens.append(self.consume().value)
        return {"type": "STATEMENT", "verb": first.upper(), "text": " ".join(tokens)}

    def peek(self, offset=0) -> Optional[Token]:
        idx = self.pos + offset
        if 0 <= idx < self.length:
            return self.tokens[idx]
        return None

    def consume(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cobolparser.py <filename>")
        sys.exit(1)
        
    filename = sys.argv[1]
    parser = CobolParser(filename)
    parser.parse()
    with open("output.json", "w") as f:
        f.write(json.dumps(parser.parsed_data, indent=4))
