"""Fix anonymization service - remove portfolio patterns, keep only GitHub, LinkedIn, Email, Phone"""

file_path = "app/services/resume_anonymization_service.py"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the problematic section
new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    if skip_until > 0 and i < skip_until:
        continue
    
    # Found the start of Step 3
    if i < len(lines) - 1 and '# Step 3: Redact clickable links' in line:
        # Add the line
        new_lines.append("                # Step 3: Redact clickable links (GitHub, LinkedIn, Email only)\n")
        skip_until = i + 1
        
        # Find the end of this section (where "# Apply all redactions" appears)
        for j in range(i + 1, len(lines)):
            if '# Apply all redactions on this page' in lines[j]:
                # Insert new code
                new_lines.append("                links = page.get_links()\n")
                new_lines.append("                for link in links:\n")
                new_lines.append("                    if 'uri' in link:\n")
                new_lines.append("                        uri = link['uri'].lower()\n")
                new_lines.append("                        should_redact = False\n")
                new_lines.append("                        \n")
                new_lines.append("                        # Redact LinkedIn links\n")
                new_lines.append("                        if 'linkedin.com' in uri:\n")
                new_lines.append("                            should_redact = True\n")
                new_lines.append("                            logger.info(f\"Redacting LinkedIn clickable link\")\n")
                new_lines.append("                        \n")
                new_lines.append("                        # Redact GitHub links\n")
                new_lines.append("                        elif 'github.com' in uri:\n")
                new_lines.append("                            should_redact = True\n")
                new_lines.append("                            logger.info(f\"Redacting GitHub clickable link\")\n")
                new_lines.append("                        \n")
                new_lines.append("                        # Redact email links\n")
                new_lines.append("                        elif 'mailto:' in uri or '@' in uri:\n")
                new_lines.append("                            should_redact = True\n")
                new_lines.append("                            logger.info(f\"Redacting email clickable link\")\n")
                new_lines.append("                        \n")
                new_lines.append("                        # Redact email provider links\n")
                new_lines.append("                        elif any(provider in uri for provider in ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com']):\n")
                new_lines.append("                            should_redact = True\n")
                new_lines.append("                            logger.info(f\"Redacting email provider clickable link\")\n")
                new_lines.append("                        \n")
                new_lines.append("                        # Black out completely and make unclickable\n")
                new_lines.append("                        if should_redact:\n")
                new_lines.append("                            rect = fitz.Rect(link['from'])\n")
                new_lines.append("                            page.add_redact_annot(rect, fill=(0, 0, 0))\n")
                new_lines.append("                            total_redactions += 1\n")
                new_lines.append("                \n")
                
                # Add the "Apply all redactions" line
                new_lines.append(lines[j])
                skip_until = j + 1
                break
    else:
        new_lines.append(line)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Fixed anonymization service!")
print("Now redacts ONLY: Username, GitHub, LinkedIn, Email/Gmail, Phone")
print("Portfolio links (.github.io, .vercel.app, etc.) are NO LONGER redacted")
