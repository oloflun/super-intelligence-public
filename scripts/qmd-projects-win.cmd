@echo off
set "HOME=%USERPROFILE%"
set "XDG_CACHE_HOME=%USERPROFILE%\.cache"
set "XDG_CONFIG_HOME=%USERPROFILE%\.config"
set "NODE_LLAMA_CPP_BUILD_BACKEND=cpu"
if /I "%1"=="embed" (
  echo Project index is keyword/AST-only by design; embeddings are disabled to avoid RAM spikes. 1>&2
  exit /b 2
)
node "%APPDATA%\npm\node_modules\@tobilu\qmd\dist\cli\qmd.js" --index projects %*
