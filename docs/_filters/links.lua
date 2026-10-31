-- Links to a folder work on GitHub, which shows the folder's README. On the site they
-- need a page, so point them at the folder's summary (index.qmd) if it has one, or its README.
-- The README in the root folder is the home page (index.qmd includes it), so links to it go there.

local function exists(path)
  local file = io.open(path, 'r')
  if file then file:close() end
  return file ~= nil
end

local function is_folder(path)
  local file = io.open(path, 'r')
  local found = file:read(1)
  file:close()
  return found == nil
end

function Link(link)
  link.content = link.content:walk({Link = function(inner) -- A file name that is already inside a link stays as it was
    if inner.classes:includes('file-link') then return inner.content end
  end})
  local target = link.target
  if target:match('^%a[%w+.-]*:') or target:match('^[#/]') then return link end -- A URL, an anchor, or a path from the root
  local up, rest = target:match('^([./]*)docs/(.*)$') -- A link from outside docs/ (the root README, or the examples), which are here on the site
  if up then
    target = up .. rest
    link.target = target
  end
  local path, anchor = target:match('^([^#]*)(.*)$')
  local here = pandoc.path.directory(quarto.doc.input_file)
  local root = path:match('^(.*)README%.md$')
  if root and exists(pandoc.path.join({here, root, '_quarto.yml'})) then -- The root README is the home page
    link.target = root .. 'index.qmd' .. anchor
    return link
  end
  local last = path:gsub('/+$', ''):match('([^/]*)$')
  if last:match('%.%w+$') and last ~= '..' then return link end -- A file, not a folder
  local folder = pandoc.path.join({here, path})
  for _, name in ipairs({'index.qmd', 'README.md'}) do
    if exists(pandoc.path.join({folder, name})) then
      link.target = pandoc.path.join({path, name}) .. anchor
      return link
    end
  end
  return link
end

-- A file named in the text (`original/sir.py`, `reference/`) links to that file on GitHub, if it is
-- there next to the page. Markdown files are left alone: they are pages of the site.
local repo = 'https://github.com/starsimhub/lingua_franca_design/'

function Code(code)
  local name = code.text
  if name:match('[%s*]') or name:match('^[/.]') or name:match('%.q?md$') then return nil end
  if not (name:match('%.%w+$') or name:match('/$')) then return nil end
  local path = pandoc.path.join({pandoc.path.directory(quarto.doc.input_file), name})
  if not exists(path) then return nil end
  local kind = is_folder(path) and 'tree' or 'blob'
  local relative = pandoc.path.make_relative(path, quarto.project.directory)
  if not (relative:match('^examples/') or relative:match('^vignettes/')) then relative = 'docs/' .. relative end -- Those two are linked into docs/
  local target = repo .. kind .. '/main/' .. relative
  return pandoc.Link({code}, target, '', pandoc.Attr('', {'file-link'}))
end
