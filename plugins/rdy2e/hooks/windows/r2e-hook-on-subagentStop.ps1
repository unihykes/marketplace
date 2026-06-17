param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")


class R2eHookSubagentStopInputBody {
  [string]$session_id
  [string]$subagent_type
  [string]$status
  [string]$task
  [string]$description
  [string]$summary
  [long]$duration_ms
  [int]$message_count
  [int]$tool_call_count
  [int]$loop_count
  [string[]]$modified_files
  [string]$agent_transcript_path
  [hashtable]$others

  R2eHookSubagentStopInputBody() {
    $this.duration_ms = 0
    $this.message_count = 0
    $this.tool_call_count = 0
    $this.loop_count = 0
    $this.modified_files = @()
  }

  [string] ToJsonString() {
    $h = @{
      subagent_type          = $this.subagent_type
      status                 = $this.status
      task                   = $this.task
      description            = $this.description
      summary                = $this.summary
      duration_ms            = $this.duration_ms
      message_count          = $this.message_count
      tool_call_count        = $this.tool_call_count
      loop_count             = $this.loop_count
      modified_files         = $this.modified_files
      agent_transcript_path  = $this.agent_transcript_path
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Set-SubagentStopHookFallbackJsonIntField {
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

function Set-SubagentStopHookFallbackJsonLongField {
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
    return $head, ([R2eHookSubagentStopInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookSubagentStopInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst subagent_type $bodyStr
    Set-HookFallbackJsonQuotedField $inst status $bodyStr
    Set-HookFallbackJsonQuotedField $inst task $bodyStr -Convert { param($cap) '...' }
    Set-HookFallbackJsonQuotedField $inst description $bodyStr
    Set-HookFallbackJsonQuotedField $inst summary $bodyStr
    Set-SubagentStopHookFallbackJsonLongField $inst duration_ms $bodyStr
    Set-SubagentStopHookFallbackJsonIntField $inst message_count $bodyStr
    Set-SubagentStopHookFallbackJsonIntField $inst tool_call_count $bodyStr
    Set-SubagentStopHookFallbackJsonIntField $inst loop_count $bodyStr
    Set-HookFallbackJsonQuotedField $inst agent_transcript_path $bodyStr
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookSubagentStopInputBody]::new()

    if ($obj.PSObject.Properties["session_id"]) {
      $v = $obj.session_id
      if ($null -ne $v) {
        $inst.session_id = Get-PrettyUuid -Id ([string]$v)
      }
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["subagent_type"]) {
      $inst.subagent_type = [string]$obj.subagent_type
      $obj.PSObject.Properties.Remove("subagent_type")
    }
    if ($obj.PSObject.Properties["status"]) {
      $inst.status = [string]$obj.status
      $obj.PSObject.Properties.Remove("status")
    }
    if ($obj.PSObject.Properties["task"]) {
      $inst.task = '...'
      $obj.PSObject.Properties.Remove("task")
    }
    if ($obj.PSObject.Properties["description"]) {
      $inst.description = [string]$obj.description
      $obj.PSObject.Properties.Remove("description")
    }
    if ($obj.PSObject.Properties["summary"]) {
      $inst.summary = [string]$obj.summary
      $obj.PSObject.Properties.Remove("summary")
    }
    if ($obj.PSObject.Properties["duration_ms"]) {
      $v = $obj.duration_ms
      if ($null -ne $v) {
        $inst.duration_ms = [long]$v
      }
      $obj.PSObject.Properties.Remove("duration_ms")
    }
    if ($obj.PSObject.Properties["message_count"]) {
      $v = $obj.message_count
      if ($null -ne $v) {
        $inst.message_count = [int]$v
      }
      $obj.PSObject.Properties.Remove("message_count")
    }
    if ($obj.PSObject.Properties["tool_call_count"]) {
      $v = $obj.tool_call_count
      if ($null -ne $v) {
        $inst.tool_call_count = [int]$v
      }
      $obj.PSObject.Properties.Remove("tool_call_count")
    }
    if ($obj.PSObject.Properties["loop_count"]) {
      $v = $obj.loop_count
      if ($null -ne $v) {
        $inst.loop_count = [int]$v
      }
      $obj.PSObject.Properties.Remove("loop_count")
    }
    if ($obj.PSObject.Properties["modified_files"]) {
      $mf = $obj.modified_files
      if ($null -ne $mf) {
        if ($mf -is [System.Array]) {
          $inst.modified_files = @($mf | ForEach-Object { [string]$_ })
        } elseif ($mf -is [string]) {
          $inst.modified_files = @($mf)
        }
      }
      $obj.PSObject.Properties.Remove("modified_files")
    }
    if ($obj.PSObject.Properties["agent_transcript_path"]) {
      $v = $obj.agent_transcript_path
      if ($null -ne $v) {
        $inst.agent_transcript_path = [string]$v
      }
      $obj.PSObject.Properties.Remove("agent_transcript_path")
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
    $inst = [R2eHookSubagentStopInputBody]::new()
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


# Hook: subagentStop
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





