param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")


class R2eHookStopInputBody {
  [string]$session_id
  [string]$status
  [int]$loop_count
  [long]$output_tokens
  [long]$input_tokens
  [long]$cache_read_tokens
  [long]$cache_write_tokens
  [hashtable]$others

  R2eHookStopInputBody() {
    $this.loop_count = 0
    $this.output_tokens = 0
    $this.input_tokens = 0
    $this.cache_read_tokens = 0
    $this.cache_write_tokens = 0
  }

  [string] ToJsonString() {
    $h = @{
      status            = $this.status
      loop_count        = $this.loop_count
      output_tokens     = $this.output_tokens
      input_tokens      = $this.input_tokens
      cache_read_tokens = $this.cache_read_tokens
      cache_write_tokens = $this.cache_write_tokens
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Set-StopHookFallbackJsonIntField {
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

function Set-StopHookFallbackJsonLongField {
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

function Get-HookInputBody {
  $head, $bodyStr = Get-HookInputHeadAndBody

  if ([string]::IsNullOrWhiteSpace($bodyStr)) {
    return $head, ([R2eHookStopInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookStopInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst status $bodyStr
    Set-StopHookFallbackJsonIntField $inst loop_count $bodyStr
    Set-StopHookFallbackJsonLongField $inst output_tokens $bodyStr
    Set-StopHookFallbackJsonLongField $inst input_tokens $bodyStr
    Set-StopHookFallbackJsonLongField $inst cache_read_tokens $bodyStr
    Set-StopHookFallbackJsonLongField $inst cache_write_tokens $bodyStr
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookStopInputBody]::new()

    if ($obj.PSObject.Properties["session_id"]) {
      $v = $obj.session_id
      if ($null -ne $v) {
        $inst.session_id = Get-PrettyUuid -Id ([string]$v)
      }
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["status"]) {
      $v = $obj.status
      if ($null -ne $v) {
        $inst.status = [string]$v
      }
      $obj.PSObject.Properties.Remove("status")
    }
    if ($obj.PSObject.Properties["loop_count"]) {
      $v = $obj.loop_count
      if ($null -ne $v) {
        $inst.loop_count = [int]$v
      }
      $obj.PSObject.Properties.Remove("loop_count")
    }

    $tokenFields = @(
      'output_tokens',
      'input_tokens',
      'cache_read_tokens',
      'cache_write_tokens'
    )
    foreach ($tf in $tokenFields) {
      if ($obj.PSObject.Properties[$tf]) {
        $v = $obj.$tf
        if ($null -ne $v) {
          switch ($tf) {
            'output_tokens' { $inst.output_tokens = [long]$v }
            'input_tokens' { $inst.input_tokens = [long]$v }
            'cache_read_tokens' { $inst.cache_read_tokens = [long]$v }
            'cache_write_tokens' { $inst.cache_write_tokens = [long]$v }
          }
        }
        $obj.PSObject.Properties.Remove($tf)
      }
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
    $inst = [R2eHookStopInputBody]::new()
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }
}

<#
// Output
{
  "followup_message": "<message text>"
}
#>
function Build-HookResponse {
  <#
    生成传给 Cursor hook 的应答 JSON 字符串（不写 stdout）；调用方对返回值自行 Write-Output。
    仅返回注释约定的输出字段。
  #>
  $payload = @{
    followup_message = ""
  }
  return ($payload | ConvertTo-Json -Compress)
}


# Hook: stop
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





