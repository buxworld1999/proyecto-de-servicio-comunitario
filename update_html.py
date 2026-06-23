import re

html_path = r'c:\games\proyectos visual\python\proyecto-de-servicio-comunitario-main-pruebas\templates\estudiantes\registro_estudiantes.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add values to normal inputs
def replace_input(match):
    full_match = match.group(0)
    name = match.group(1)
    
    # Don't modify cedula since it's already modified
    if name == 'cedula':
        return full_match
        
    if 'value=' in full_match:
        return full_match
        
    if 'type="file"' in full_match:
        return full_match
        
    # Append value attribute
    return full_match.replace('>', f' value="{{{{ estudiante.{name} if estudiante and estudiante.{name} else \'\' }}}}">')

content = re.sub(r'<input\s+[^>]*name="([^"]+)"[^>]*>', replace_input, content)

# Add selected to options
def replace_select(match):
    full_match = match.group(0)
    name = match.group(1)
    options_block = match.group(2)
    
    def option_replacer(opt_match):
        opt_full = opt_match.group(0)
        opt_val = opt_match.group(1)
        # Inject jinja selected logic
        return opt_full.replace('>', f' {{{{ \'selected\' if estudiante and estudiante.{name} == \'{opt_val}\' else \'\' }}}}>')
        
    new_options = re.sub(r'<option\s+value="([^"]+)"[^>]*>', option_replacer, options_block)
    return full_match.replace(options_block, new_options)

content = re.sub(r'<select\s+[^>]*name="([^"]+)"[^>]*>(.*?)</select>', replace_select, content, flags=re.DOTALL)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
