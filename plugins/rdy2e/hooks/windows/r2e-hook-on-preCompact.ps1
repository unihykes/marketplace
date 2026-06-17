param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")


class R2eHookPreCompactInputBody {
  [string]$session_id
  [string]$trigger
  [double]$context_usage_percent
  [long]$context_tokens
  [long]$context_window_size
  [int]$message_count
  [int]$messages_to_compact
  [bool]$is_first_compaction
  [hashtable]$others

  R2eHookPreCompactInputBody() {
    $this.context_usage_percent = 0.0
    $this.context_tokens = 0
    $this.context_window_size = 0
    $this.message_count = 0
    $this.messages_to_compact = 0
    $this.is_first_compaction = $false
  }

  [string] ToJsonString() {
    $h = @{
      trigger                 = $this.trigger
      context_usage_percent   = $this.context_usage_percent
      context_tokens          = $this.context_tokens
      context_window_size     = $this.context_window_size
      message_count           = $this.message_count
      messages_to_compact     = $this.messages_to_compact
      is_first_compaction     = $this.is_first_compaction
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Set-PreCompactHookFallbackJsonDoubleField {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true, Position = 0)]
    $Target,

    [Parameter(Mandatory = $true, Position = 1)]
    [ValidateNotNullOrEmpty()]
    [string]$MemberName,

    [Parameter(Mandatory = $true, Position = 2)]
    [AllowEmptyString()]
    [string]$Text,

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$JsonFieldName
  )
  $key = if ($PSBoundParameters.ContainsKey('JsonFieldName')) { $JsonFieldName } else { $MemberName }
  $pattern = '"' + [regex]::Escape($key) + '"\s*:\s*(-?\d+(?:\.\d+)?)'
  $cap = Get-HookFallbackRegexCapture -Text $Text -Pattern $pattern
  if ($null -eq $cap) { return }

  $Target.$MemberName = [double]$cap
}

function Set-PreCompactHookFallbackJsonLongField {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true, Position = 0)]
    $Target,

    [Parameter(Mandatory = $true, Position = 1)]
    [ValidateNotNullOrEmpty()]
    [string]$MemberName,

    [Parameter(Mandatory = $true, Position = 2)]
    [AllowEmptyString()]
    [string]$Text,

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$JsonFieldName
  )
  $key = if ($PSBoundParameters.ContainsKey('JsonFieldName')) { $JsonFieldName } else { $MemberName }
  $pattern = '"' + [regex]::Escape($key) + '"\s*:\s*(-?\d+)'
  $cap = Get-HookFallbackRegexCapture -Text $Text -Pattern $pattern
  if ($null -eq $cap) { return }

  $Target.$MemberName = [long]$cap
}

function Set-PreCompactHookFallbackJsonIntField {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true, Position = 0)]
    $Target,

    [Parameter(Mandatory = $true, Position = 1)]
    [ValidateNotNullOrEmpty()]
    [string]$MemberName,

    [Parameter(Mandatory = $true, Position = 2)]
    [AllowEmptyString()]
    [string]$Text,

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$JsonFieldName
  )
  $key = if ($PSBoundParameters.ContainsKey('JsonFieldName')) { $JsonFieldName } else { $MemberName }
  $pattern = '"' + [regex]::Escape($key) + '"\s*:\s*(-?\d+)'
  $cap = Get-HookFallbackRegexCapture -Text $Text -Pattern $pattern
  if ($null -eq $cap) { return }

  $Target.$MemberName = [int]$cap
}

function Get-HookInputBody {
  $head, $bodyStr = Get-HookInputHeadAndBody

  if ([string]::IsNullOrWhiteSpace($bodyStr)) {
    return $head, ([R2eHookPreCompactInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookPreCompactInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst trigger $bodyStr
    Set-PreCompactHookFallbackJsonDoubleField $inst context_usage_percent $bodyStr
    Set-PreCompactHookFallbackJsonLongField $inst context_tokens $bodyStr
    Set-PreCompactHookFallbackJsonLongField $inst context_window_size $bodyStr
    Set-PreCompactHookFallbackJsonIntField $inst message_count $bodyStr
    Set-PreCompactHookFallbackJsonIntField $inst messages_to_compact $bodyStr
    Set-HookFallbackJsonBoolField $inst is_first_compaction $bodyStr
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookPreCompactInputBody]::new()

    if ($obj.PSObject.Properties["session_id"]) {
      $v = $obj.session_id
      if ($null -ne $v) {
        $inst.session_id = Get-PrettyUuid -Id ([string]$v)
      }
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["trigger"]) {
      $v = $obj.trigger
      if ($null -ne $v) {
        $inst.trigger = [string]$v
      }
      $obj.PSObject.Properties.Remove("trigger")
    }
    if ($obj.PSObject.Properties["context_usage_percent"]) {
      $v = $obj.context_usage_percent
      if ($null -ne $v) {
        $inst.context_usage_percent = [double]$v
      }
      $obj.PSObject.Properties.Remove("context_usage_percent")
    }
    if ($obj.PSObject.Properties["context_tokens"]) {
      $v = $obj.context_tokens
      if ($null -ne $v) {
        $inst.context_tokens = [long]$v
      }
      $obj.PSObject.Properties.Remove("context_tokens")
    }
    if ($obj.PSObject.Properties["context_window_size"]) {
      $v = $obj.context_window_size
      if ($null -ne $v) {
        $inst.context_window_size = [long]$v
      }
      $obj.PSObject.Properties.Remove("context_window_size")
    }
    if ($obj.PSObject.Properties["message_count"]) {
      $v = $obj.message_count
      if ($null -ne $v) {
        $inst.message_count = [int]$v
      }
      $obj.PSObject.Properties.Remove("message_count")
    }
    if ($obj.PSObject.Properties["messages_to_compact"]) {
      $v = $obj.messages_to_compact
      if ($null -ne $v) {
        $inst.messages_to_compact = [int]$v
      }
      $obj.PSObject.Properties.Remove("messages_to_compact")
    }
    if ($obj.PSObject.Properties["is_first_compaction"]) {
      $inst.is_first_compaction = [bool]$obj.is_first_compaction
      $obj.PSObject.Properties.Remove("is_first_compaction")
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
    $inst = [R2eHookPreCompactInputBody]::new()
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


# Hook: preCompact
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





