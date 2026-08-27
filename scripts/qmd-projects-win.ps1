$env:HOME = $env:USERPROFILE
$env:XDG_CACHE_HOME = Join-Path $env:USERPROFILE ".cache"
$env:XDG_CONFIG_HOME = Join-Path $env:USERPROFILE ".config"
$env:NODE_LLAMA_CPP_BUILD_BACKEND = "cpu"
if ($args.Count -gt 0 -and $args[0] -ieq "embed") {
  Write-Error "Project index is keyword/AST-only by design; embeddings are disabled to avoid RAM spikes."
  exit 2
}
$qmd = Join-Path $env:APPDATA "npm\node_modules\@tobilu\qmd\dist\cli\qmd.js"
& node $qmd --index projects @args
