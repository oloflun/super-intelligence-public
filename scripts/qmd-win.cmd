@echo off
set "HOME=%USERPROFILE%"
set "XDG_CACHE_HOME=%USERPROFILE%\.cache"
set "XDG_CONFIG_HOME=%USERPROFILE%\.config"
set "INDEX_PATH=%USERPROFILE%\.cache\qmd\index.sqlite"
set "NODE_LLAMA_CPP_BUILD_BACKEND=cpu"
if /I "%1"=="embed" if not "%QMD_ALLOW_HEAVY_EMBED%"=="1" (
  echo qmd embed is disabled in the normal wrapper because it is RAM-heavy. 1>&2
  echo Use qmd search, or set QMD_ALLOW_HEAVY_EMBED=1 deliberately for a curated embed run. 1>&2
  exit /b 2
)
node "%APPDATA%\npm\node_modules\@tobilu\qmd\dist\cli\qmd.js" %*
