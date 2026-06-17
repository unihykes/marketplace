param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")


class R2eHookBeforeSubmitPromptInputBody {
  [string]$session_id
  [string]$composer_mode
  [string]$prompt
  [System.Object[]]$attachments
  [hashtable]$others

  R2eHookBeforeSubmitPromptInputBody() {
    $this.attachments = @()
  }

  [string] ToJsonString() {
    $h = @{
      composer_mode = $this.composer_mode
      prompt        = $this.prompt
      attachments = $this.attachments
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Get-HookInputBody {
  $head, $bodyStr = Get-HookInputHeadAndBody

  if ([string]::IsNullOrWhiteSpace($bodyStr)) {
    return $head, ([R2eHookBeforeSubmitPromptInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookBeforeSubmitPromptInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst composer_mode $bodyStr
    Set-HookFallbackJsonQuotedField $inst prompt $bodyStr -Convert { param($cap) '...' }
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookBeforeSubmitPromptInputBody]::new()

    if ($obj.PSObject.Properties["session_id"]) {
      $v = $obj.session_id
      if ($null -ne $v) {
        $inst.session_id = Get-PrettyUuid -Id ([string]$v)
      }
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["composer_mode"]) {
      $v = $obj.composer_mode
      if ($null -ne $v) {
        $inst.composer_mode = [string]$v
      }
      $obj.PSObject.Properties.Remove("composer_mode")
    }
    if ($obj.PSObject.Properties["prompt"]) {
      $inst.prompt = '...'
      $obj.PSObject.Properties.Remove("prompt")
    }
    if ($obj.PSObject.Properties["attachments"]) {
      $inst.attachments = ConvertFrom-R2eHookAttachmentsForLog -Attachments $obj.attachments
      $obj.PSObject.Properties.Remove("attachments")
    }

    foreach ($prop in $obj.PSObject.Properties) {
      if ($null -eq $inst.others) {
        $inst.others = @{}
      }
      $inst.others[$prop.Name] = $prop.Value
    }
    return $head, $inst
  }
  catch {
    $inst = [R2eHookBeforeSubmitPromptInputBody]::new()
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }
}

function Build-HookResponse {
  <#
    生成传给 Cursor hook 的应答 JSON 字符串（不写 stdout）；调用方对返回值自行 Write-Output。
    默认：permission 放行。
  #>
  $payload = @{
    permission = "allow"
    user_message = "ok"
  }
  return ($payload | ConvertTo-Json -Compress)
}


# Hook: beforeSubmitPrompt
Set-HookOutputUtf8
$head, $body = Get-HookInputBody
Add-Content -Encoding utf8 -Path (Get-HookProjectLogPath) -Value (
  "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')]" +
    "[$($head.WorkspaceName)]" +
    "[$(Get-PrettyUuid -Id $head.ConversationId)]" +
    "[$(Get-PrettyUuid -Id $head.GenerationId)]" +
    "[$($head.ModelName)]" +
    "[$($head.HookEventName)]" +
    " " +
    $( $body.ToJsonString() )
)
$response = Build-HookResponse
Write-Output $response
exit 0





