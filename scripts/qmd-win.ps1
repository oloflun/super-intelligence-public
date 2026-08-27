$env:HOME = $env:USERPROFILE
$env:XDG_CACHE_HOME = Join-Path $env:USERPROFILE ".cache"
$env:XDG_CONFIG_HOME = Join-Path $env:USERPROFILE ".config"
$env:INDEX_PATH = Join-Path $env:USERPROFILE ".cache\qmd\index.sqlite"
$env:NODE_LLAMA_CPP_BUILD_BACKEND = "cpu"
if ($args.Count -gt 0 -and $args[0] -ieq "embed" -and $env:QMD_ALLOW_HEAVY_EMBED -ne "1") {
  Write-Error "qmd embed is disabled in the normal wrapper because it is RAM-heavy. Use qmd search, or set QMD_ALLOW_HEAVY_EMBED=1 deliberately for a curated embed run."
  exit 2
}
$qmd = Join-Path $env:APPDATA "npm\node_modules\@tobilu\qmd\dist\cli\qmd.js"
& node $qmd @args
