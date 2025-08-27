#!/usr/bin/env python3
"""
Comprehensive flake8 fixer for 10/10 code quality.
"""

import os
import re

def fix_indentation_issues(content):
    """Fix E128 and E131 indentation issues."""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix E128: continuation line under-indented for visual indent
        if line.strip().startswith('"') and i > 0:
            prev_line = lines[i-1].rstrip()
            if prev_line.endswith('(') or prev_line.endswith(','):
                indent_match = re.match(r'^(\s*)', prev_line)
                if indent_match:
                    base_indent = indent_match.group(1)
                    new_indent = base_indent + '    '
                    line = new_indent + line.lstrip()
        
        # Fix E131: continuation line unaligned for hanging indent
        if line.strip().startswith('"') and i > 0:
            prev_line = lines[i-1].rstrip()
            if prev_line.endswith('('):
                # Find the opening parenthesis position
                paren_pos = prev_line.rfind('(')
                if paren_pos > 0:
                    # Align with the character after the opening parenthesis
                    align_pos = paren_pos + 1
                    new_indent = ' ' * align_pos
                    line = new_indent + line.lstrip()
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_blank_line_issues(content):
    """Fix E302 and E305 blank line issues."""
    # Fix E302: expected 2 blank lines, found 1
    content = re.sub(r'(\nclass [^\n]*:\n[^\n]*\n)\n(\n)', r'\1\2', content)
    content = re.sub(r'(\ndef [^\n]*:\n[^\n]*\n)\n(\n)', r'\1\2', content)
    
    # Fix E305: expected 2 blank lines after class or function definition, found 1
    content = re.sub(r'(\nclass [^\n]*:\n[^\n]*\n)\n(\n)', r'\1\2', content)
    content = re.sub(r'(\ndef [^\n]*:\n[^\n]*\n)\n(\n)', r'\1\2', content)
    
    return content

def fix_file(filepath):
    """Fix all flake8 issues in a file."""
    print(f"Fixing {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix whitespace issues
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)  # W293
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)  # W291
    
    # Fix indentation issues
    content = fix_indentation_issues(content)
    
    # Fix blank line issues
    content = fix_blank_line_issues(content)
    
    # Fix E303: too many blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Fix all Python files."""
    src_dir = 'src'
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                fix_file(filepath)

if __name__ == "__main__":
    main()
