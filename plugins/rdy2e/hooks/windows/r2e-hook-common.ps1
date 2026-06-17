# 对应 Cursor hook 官方文档中的基础字段（conversation_id、model 等
class R2eHookInputHead {
  [string]$ConversationId = "-"
  [string]$GenerationId = "-"
  [string]$ModelName = "-"
  [string]$HookEventName = "-"
  [string]$WorkspaceName = "-"
  [bool]$IsValidJson = $true
}

# 统一 stdout 编码，避免中文输出乱码
function Set-HookOutputUtf8 {
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
}

<#
  从整体 JSON 文本上按正则取第一个捕获组（用于非法 JSON 时的降级解析）。
  无匹配时返回 $null。
#>
function Get-HookFallbackRegexCapture {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true)]
    [AllowEmptyString()]
    [string]$Text,

    [Parameter(Mandatory = $true)]
    [string]$Pattern,

    [Parameter(Mandatory = $false)]
    [int]$CaptureGroup = 1
  )
  if ([string]::IsNullOrWhiteSpace($Text)) {
    return $null
  }
  $m = [System.Text.RegularExpressions.Regex]::Match($Text, $Pattern)
  if (-not $m.Success -or $CaptureGroup -lt 0 -or $CaptureGroup -ge $m.Groups.Count) {
    return $null
  }
  return [string]$m.Groups[$CaptureGroup].Value
}

<#
  非法 JSON 降级：解析 "jsonField"\s*:\s*"捕获" 写入对象成员；-JsonFieldName 缺省时与 MemberName 相同。
  无匹配不写回。
#>
function Set-HookFallbackJsonQuotedField {
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
    [string]$JsonFieldName,

    [Parameter(Mandatory = $false)]
    [scriptblock]$Convert = $null
  )
  $key = if ($PSBoundParameters.ContainsKey('JsonFieldName')) { $JsonFieldName } else { $MemberName }
  $pattern = '"' + [regex]::Escape($key) + '"\s*:\s*"([^"]*)"'
  $cap = Get-HookFallbackRegexCapture -Text $Text -Pattern $pattern
  if ($null -eq $cap) { return }

  if ($null -eq $Convert) {
    $Target.$MemberName = $cap
  } else {
    $Target.$MemberName = & $Convert $cap
  }
}

<#
  非法 JSON 降级：解析 "jsonField"\s*:\s*(true|false)。
#>
function Set-HookFallbackJsonBoolField {
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
  $pattern = '"' + [regex]::Escape($key) + '"\s*:\s*(true|false)'
  $cap = Get-HookFallbackRegexCapture -Text $Text -Pattern $pattern
  if ($null -eq $cap) { return }

  $Target.$MemberName = [bool]::Parse($cap)
}

function Set-HookFallbackWorkspaceNameFromRoots {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true, Position = 0)]
    $Head,

    [Parameter(Mandatory = $true, Position = 1)]
    [AllowEmptyString()]
    [string]$Text
  )
  $v = Get-HookFallbackRegexCapture -Text $Text -Pattern '"workspace_roots"\s*:\s*\[\s*"([^"]*)"'
  if ($null -eq $v) { return }
  if ([string]::IsNullOrWhiteSpace($v)) { return }

  $normalizedRoot = ($v -replace "\\", "/").TrimEnd("/")
  $leaf = Split-Path -Path $normalizedRoot -Leaf
  if (-not [string]::IsNullOrWhiteSpace($leaf)) {
    $Head.WorkspaceName = $leaf
  }
}

$script:R2eHookLogPathPropertyNames = [System.Collections.Generic.HashSet[string]]::new(
  [StringComparer]::OrdinalIgnoreCase)
foreach ($n in @(
    'cwd', 'file_path', 'path', 'root', 'workspace_path', 'workspacePath',
    'workspace_roots', 'file', 'target', 'target_file', 'directory', 'folder',
    'uri', 'absolute_path', 'relative_path', 'working_directory', 'workspaceFolder',
    'rootPath', 'filePath', 'transcript_path', 'agent_transcript_path', 'script_path'
  )) {
  [void]$script:R2eHookLogPathPropertyNames.Add($n)
}

$script:R2eHookLogSkipPathNormalizeNames = [System.Collections.Generic.HashSet[string]]::new(
  [StringComparer]::OrdinalIgnoreCase)
foreach ($n in @(
    'old_string', 'new_string', 'replacement', 'pattern', 'regex',
    'command', 'output', 'prompt', 'content', 'text', 'user_message',
    'message', 'result_json', 'thinking', 'response', 'description'
  )) {
  [void]$script:R2eHookLogSkipPathNormalizeNames.Add($n)
}

function Test-R2eHookStringLooksLikeWindowsPath {
  param([AllowEmptyString()] [string]$s)
  if ([string]::IsNullOrWhiteSpace($s)) { return $false }
  if ($s -match '^[A-Za-z]:[\\/]') { return $true }
  if ($s -match '^\\\\\?\\') { return $true }
  if ($s -match '^\\\\[^\\]+\\') { return $true }
  return $false
}

<#
  仅用于日志：将 Windows 路径中的反斜杠改为正斜杠，避免 ConvertTo-Json 产生大量 "\\" 转义、难以阅读。
  通过「属性名属于路径类」或「整串像绝对路径」判定；old_string 等键不处理以免误改编辑片段。
#>
function Normalize-R2eHookLogPathsInTree {
  param(
    [AllowNull()]
    $Node,

    [Parameter(Mandatory = $false)]
    [string]$PropertyName = ""
  )
  if ($null -eq $Node) { return $null }

  if ($Node -is [string]) {
    $s = $Node
    $skip = ($PropertyName -ne "" -and $script:R2eHookLogSkipPathNormalizeNames.Contains($PropertyName))
    if ($skip) { return $s }
    $pathKey = ($PropertyName -ne "" -and $script:R2eHookLogPathPropertyNames.Contains($PropertyName))
    $looksPath = (Test-R2eHookStringLooksLikeWindowsPath $s)
    if (($pathKey -or $looksPath) -and ($s.IndexOf([char]'\') -ge 0)) {
      return ($s -replace '\\', '/')
    }
    return $s
  }

  if ($Node -is [bool] -or $Node -is [int] -or $Node -is [long] -or $Node -is [double] -or $Node -is [decimal]) {
    return $Node
  }

  if ($Node -is [hashtable] -or $Node -is [System.Collections.IDictionary]) {
    foreach ($k in @($Node.Keys)) {
      $ks = [string]$k
      $Node[$k] = Normalize-R2eHookLogPathsInTree -Node $Node[$k] -PropertyName $ks
    }
    return $Node
  }

  if ($Node -is [System.Management.Automation.PSCustomObject]) {
    foreach ($p in @($Node.PSObject.Properties)) {
      $newV = Normalize-R2eHookLogPathsInTree -Node $p.Value -PropertyName $p.Name
      $Node | Add-Member -NotePropertyName $p.Name -NotePropertyValue $newV -Force
    }
    return $Node
  }

  if ($Node -is [System.Collections.IEnumerable] -and $Node -isnot [string]) {
    $list = [System.Collections.ArrayList]::new()
    foreach ($el in $Node) {
      [void]$list.Add((Normalize-R2eHookLogPathsInTree -Node $el -PropertyName $PropertyName))
    }
    return @($list)
  }

  return $Node
}

<#
  写入按日归档的 hook 事件日志前统一 JSON 序列化：
  先深度 round-trip 再规范化路径斜杠，避免改到内存中的原始对象。
#>
function ConvertTo-R2eHookEventLogJson {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true, Position = 0)]
    $InputObject,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 2147483647)]
    [int]$Depth = 20
  )

  if ($null -eq $InputObject) {
    return 'null'
  }

  $roundTripDepth = [Math]::Max(100, $Depth)
  $json = $null
  try {
    $json = $InputObject | ConvertTo-Json -Compress -Depth $roundTripDepth -ErrorAction Stop
  } catch {
    return ($InputObject | ConvertTo-Json -Compress -Depth $Depth)
  }

  if ([string]::IsNullOrWhiteSpace($json)) {
    return ($InputObject | ConvertTo-Json -Compress -Depth $Depth)
  }

  try {
    $tree = $json | ConvertFrom-Json -ErrorAction Stop
  } catch {
    return $json
  }

  $null = Normalize-R2eHookLogPathsInTree -Node $tree
  return ($tree | ConvertTo-Json -Compress -Depth $Depth)
}

<#
  ConvertFrom-Json 得到的嵌套 JSON 对象（例如 tool_input、tool_output）为 PSCustomObject；
  拷贝为 Hashtable 便于日志序列化。字符串类型的 content、command、pattern、output 键改为 "..."；
  嵌套的 PSCustomObject 与对象数组会递归做同样处理。（pattern 用于 Grep 等工具；output 常为 shell/工具长文本。）
#>
function ConvertTo-R2eHookMaskedObjectHashtable {
  param([AllowNull()] [object]$InputObject)

  $ht = @{}
  if ($null -eq $InputObject) {
    return $ht
  }
  if ($InputObject -isnot [System.Management.Automation.PSCustomObject]) {
    return $ht
  }
  foreach ($p in $InputObject.PSObject.Properties) {
    $val = $p.Value
    if ($null -eq $val) {
      $ht[$p.Name] = $null
    } elseif ($p.Name -eq 'content' -and $val -is [string]) {
      $ht[$p.Name] = '...'
    } elseif ($p.Name -eq 'command' -and $val -is [string]) {
      $ht[$p.Name] = '...'
    } elseif ($p.Name -eq 'pattern' -and $val -is [string]) {
      $ht[$p.Name] = '...'
    } elseif ($p.Name -eq 'output' -and $val -is [string]) {
      $ht[$p.Name] = '...'
    } elseif ($val -is [System.Management.Automation.PSCustomObject]) {
      $ht[$p.Name] = ConvertTo-R2eHookMaskedObjectHashtable -InputObject $val
    } elseif ($val -is [System.Array]) {
      $list = [System.Collections.ArrayList]@()
      foreach ($el in $val) {
        if ($null -eq $el) {
          [void]$list.Add($null)
        } elseif ($el -is [System.Management.Automation.PSCustomObject]) {
          [void]$list.Add((ConvertTo-R2eHookMaskedObjectHashtable -InputObject $el))
        } else {
          [void]$list.Add($el)
        }
      }
      $ht[$p.Name] = @($list)
    } else {
      $ht[$p.Name] = $val
    }
  }
  return $ht
}

<#
  postToolUse（等）的 tool_output：可能是 PSCustomObject、JSON 字符串、数组或标量。
  ConvertTo-R2eHookMaskedObjectHashtable 仅处理对象；字符串/数组原样走入会变为空 {}，日志误判为「始终为空」。
#>
function ConvertFrom-R2eHookToolOutputForLog {
  param([AllowNull()] [object]$ToolOutput)

  if ($null -eq $ToolOutput) {
    return @{}
  }
  if ($ToolOutput -is [System.Management.Automation.PSCustomObject]) {
    return ConvertTo-R2eHookMaskedObjectHashtable -InputObject $ToolOutput
  }
  if ($ToolOutput -is [string]) {
    $s = [string]$ToolOutput
    if ([string]::IsNullOrWhiteSpace($s)) {
      return @{}
    }
    try {
      $nested = $s | ConvertFrom-Json
      return ConvertFrom-R2eHookToolOutputForLog -ToolOutput $nested
    } catch {
      return @{ _unparsed = '...' }
    }
  }
  if ($ToolOutput -is [System.Array]) {
    $items = [System.Collections.ArrayList]@()
    foreach ($el in $ToolOutput) {
      if ($el -is [System.Management.Automation.PSCustomObject]) {
        [void]$items.Add((ConvertTo-R2eHookMaskedObjectHashtable -InputObject $el))
      } elseif ($el -is [string]) {
        [void]$items.Add('...')
      } else {
        [void]$items.Add($el)
      }
    }
    return @{ _array = @($items) }
  }
  return @{ _value = $ToolOutput }
}

<#
  postToolUse：若 tool_output 与 tool_input 顶层的 file_path 指向同一路径（仅日志），将 output 侧改为 "..."
  以减少与 tool_input 的重复。官方未承诺二者总相等；故仅在字符串归一化后一致时才精简。
#>
function Apply-R2eHookPostToolUseOutputFilePathDedup {
  param(
    [hashtable]$ToolOutputHt,
    [hashtable]$ToolInputHt
  )
  if ($null -eq $ToolOutputHt -or $ToolOutputHt.Count -eq 0) { return }
  if ($null -eq $ToolInputHt -or $ToolInputHt.Count -eq 0) { return }
  if (-not ($ToolOutputHt.ContainsKey('file_path') -and $ToolInputHt.ContainsKey('file_path'))) { return }

  $out = $ToolOutputHt['file_path']
  $inn = $ToolInputHt['file_path']
  if ($null -eq $out -or $null -eq $inn) { return }
  if ($out -isnot [string] -or $inn -isnot [string]) { return }

  $a = [string]$inn
  $b = [string]$out
  if ([string]::IsNullOrWhiteSpace($a) -or [string]::IsNullOrWhiteSpace($b)) { return }

  $na = ($a -replace '\\', '/').TrimEnd('/')
  $nb = ($b -replace '\\', '/').TrimEnd('/')
  if ($na -ieq $nb) {
    $ToolOutputHt['file_path'] = '...'
  }
}

<#
  ConvertFrom-Json 得到的 tool_input（PSCustomObject）浅拷贝为 Hashtable，便于日志序列化；
  顶层键 context 改为 "..."；字符串类型的 command、pattern、output 改为 "..."；
  嵌套 PSCustomObject 与对象数组递归处理。
  非 PSCustomObject 时返回空 Hashtable（字符串形式的 tool_input 由 ConvertFrom-R2eHookMcpToolInputForLog 先解析再传入）。
#>
function ConvertTo-R2eHookMaskedToolInputHashtable {
  param([AllowNull()] [object]$InputObject)

  $ht = @{}
  if ($null -eq $InputObject) {
    return $ht
  }
  if ($InputObject -isnot [System.Management.Automation.PSCustomObject]) {
    return $ht
  }
  foreach ($p in $InputObject.PSObject.Properties) {
    $val = $p.Value
    if ($null -eq $val) {
      $ht[$p.Name] = $null
    } elseif ($p.Name -eq 'context') {
      $ht[$p.Name] = '...'
    } elseif ($p.Name -eq 'command' -and $val -is [string]) {
      $ht[$p.Name] = '...'
    } elseif ($p.Name -eq 'pattern' -and $val -is [string]) {
      $ht[$p.Name] = '...'
    } elseif ($p.Name -eq 'output' -and $val -is [string]) {
      $ht[$p.Name] = '...'
    } elseif ($val -is [System.Management.Automation.PSCustomObject]) {
      $ht[$p.Name] = ConvertTo-R2eHookMaskedToolInputHashtable -InputObject $val
    } elseif ($val -is [System.Array]) {
      $list = [System.Collections.ArrayList]@()
      foreach ($el in $val) {
        if ($null -eq $el) {
          [void]$list.Add($null)
        } elseif ($el -is [System.Management.Automation.PSCustomObject]) {
          [void]$list.Add((ConvertTo-R2eHookMaskedToolInputHashtable -InputObject $el))
        } else {
          [void]$list.Add($el)
        }
      }
      $ht[$p.Name] = @($list)
    } else {
      $ht[$p.Name] = $val
    }
  }
  return $ht
}

<#
  before/after MCP hook：将 tool_input（对象或 JSON 字符串）转为带 context、command、pattern、output 脱敏的 Hashtable，供日志序列化。
#>
function ConvertFrom-R2eHookMcpToolInputForLog {
  param([AllowNull()] [object]$ToolInput)

  if ($null -eq $ToolInput) {
    return @{}
  }
  if ($ToolInput -is [System.Management.Automation.PSCustomObject]) {
    return ConvertTo-R2eHookMaskedToolInputHashtable -InputObject $ToolInput
  }
  if ($ToolInput -is [string]) {
    $s = [string]$ToolInput
    if ([string]::IsNullOrWhiteSpace($s)) {
      return @{}
    }
    try {
      $nested = $s | ConvertFrom-Json
      if ($nested -is [System.Management.Automation.PSCustomObject]) {
        return ConvertTo-R2eHookMaskedToolInputHashtable -InputObject $nested
      }
    } catch {
      return @{ _unparsed = '...' }
    }
    return @{ _unparsed = '...' }
  }
  return @{ _value = '...' }
}

<#
  afterFileEdit：将单条 edit（PSCustomObject）浅拷贝为 Hashtable；old_string、new_string 统一为 "..."
#>
function ConvertTo-R2eHookMaskedFileEditItemHashtable {
  param([AllowNull()] [object]$InputObject)

  if ($null -eq $InputObject) {
    return @{}
  }
  if ($InputObject -isnot [System.Management.Automation.PSCustomObject]) {
    return @{ _value = '...' }
  }
  $ht = @{}
  foreach ($p in $InputObject.PSObject.Properties) {
    if ($p.Name -eq 'old_string' -or $p.Name -eq 'new_string') {
      $ht[$p.Name] = '...'
    } else {
      $ht[$p.Name] = $p.Value
    }
  }
  return $ht
}

<#
  afterFileEdit：edits 为数组或单对象时，转为 Hashtable[]，每条内的 old_string / new_string 已脱敏。
#>
function ConvertFrom-R2eHookFileEditsForLog {
  param([AllowNull()] [object]$Edits)

  if ($null -eq $Edits) {
    return @()
  }
  if ($Edits -is [System.Management.Automation.PSCustomObject]) {
    return @((ConvertTo-R2eHookMaskedFileEditItemHashtable -InputObject $Edits))
  }
  if ($Edits -isnot [System.Array]) {
    return @(@{ _value = '...' })
  }
  $out = [System.Collections.ArrayList]@()
  foreach ($item in $Edits) {
    if ($item -is [System.Management.Automation.PSCustomObject]) {
      [void]$out.Add((ConvertTo-R2eHookMaskedFileEditItemHashtable -InputObject $item))
    } else {
      [void]$out.Add(@{ _value = '...' })
    }
  }
  return @($out)
}

<#
  beforeReadFile / beforeSubmitPrompt：attachments 转为 Hashtable[]，便于日志序列化。
#>
function ConvertFrom-R2eHookAttachmentsForLog {
  param([AllowNull()] [object]$Attachments)

  if ($null -eq $Attachments) {
    return @()
  }
  if ($Attachments -is [System.Management.Automation.PSCustomObject]) {
    $ht = @{}
    foreach ($p in $Attachments.PSObject.Properties) {
      $ht[$p.Name] = $p.Value
    }
    return @($ht)
  }
  if ($Attachments -isnot [System.Array]) {
    return @(@{ _value = '...' })
  }
  $out = [System.Collections.ArrayList]@()
  foreach ($item in $Attachments) {
    if ($item -is [System.Management.Automation.PSCustomObject]) {
      $ht = @{}
      foreach ($p in $item.PSObject.Properties) {
        $ht[$p.Name] = $p.Value
      }
      [void]$out.Add($ht)
    } else {
      [void]$out.Add(@{ _value = '...' })
    }
  }
  return @($out)
}

<#
  Cursor 偶发截断 stdin，使 "text":"…… 在下一个属性前缺少闭合 "，形如:
  "text":"xxxx,"otherKey":...
  合法应为 "text":"xxxx","otherKey":...
  在首个形如 , "key": 的下一属性前、若逗号前不是 "，则插入一个 "（不假设下一键名为 input_tokens）。
#>
function Repair-R2eHookMissingClosingQuoteAfterTextValue {
  param(
    [Parameter(Mandatory = $true)]
    [AllowEmptyString()]
    [string]$Raw
  )
  if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }
  $openMm = [regex]::Match($Raw, '"text"\s*:\s*"')
  if (-not $openMm.Success) { return $null }
  $valueStart = $openMm.Index + $openMm.Length
  if ($valueStart -ge $Raw.Length) { return $null }
  $tail = $Raw.Substring($valueStart)
  $nxMm = [regex]::Match($tail, ',\s*"(?:\\.|[^"\\])*"\s*:')
  if (-not $nxMm.Success) { return $null }
  $commaRel = $nxMm.Index
  if ($commaRel -lt 1) { return $null }
  if ($tail[$commaRel - 1] -eq [char]'"') { return $null }
  $absComma = $valueStart + $commaRel
  return ($Raw.Substring(0, $absComma) + '"' + $Raw.Substring($absComma))
}

function Get-HookInputHeadAndBody {
  $stdin = [Console]::OpenStandardInput()
  $reader = New-Object System.IO.StreamReader($stdin, [System.Text.UTF8Encoding]::new($false), $true)
  $rawInput = $reader.ReadToEnd()
  $rawInput = $rawInput.TrimStart([char]0xFEFF)
  $reader.Dispose()

  $head = [R2eHookInputHead]::new()
  $bodyStr = $rawInput

  try {
    $obj = $null
    try {
      $obj = $rawInput | ConvertFrom-Json -ErrorAction Stop
    } catch {
      $ex = $_
      $repaired = Repair-R2eHookMissingClosingQuoteAfterTextValue -Raw $rawInput
      if ($null -ne $repaired) {
        try {
          $obj = $repaired | ConvertFrom-Json -ErrorAction Stop
        } catch {
          $obj = $null
        }
      }
      if ($null -eq $obj) {
        throw $ex
      }
    }
    if ($obj.PSObject.Properties["conversation_id"] -and $obj.conversation_id -is [string]) {
      $head.ConversationId = $obj.conversation_id
      $obj.PSObject.Properties.Remove("conversation_id")
    }
    if ($obj.PSObject.Properties["generation_id"] -and $obj.generation_id -is [string]) {
      $head.GenerationId = $obj.generation_id
      $obj.PSObject.Properties.Remove("generation_id")
    }
    if ($obj.PSObject.Properties["model"] -and $obj.model -is [string]) {
      $head.ModelName = $obj.model
      $obj.PSObject.Properties.Remove("model")
    }
    if ($obj.PSObject.Properties["hook_event_name"] -and $obj.hook_event_name -is [string]) {
      $head.HookEventName = $obj.hook_event_name
      $obj.PSObject.Properties.Remove("hook_event_name")
    }
    if ($obj.PSObject.Properties["workspace_roots"]) {
      $firstRoot = $null
      if ($obj.workspace_roots -is [System.Array]) {
        if ($obj.workspace_roots.Count -gt 0) {
          $firstRoot = [string]$obj.workspace_roots[0]
        }
      } elseif ($obj.workspace_roots -is [string]) {
        $firstRoot = $obj.workspace_roots
      }
      if (-not [string]::IsNullOrWhiteSpace($firstRoot)) {
        $normalizedRoot = ($firstRoot -replace "\\", "/").TrimEnd("/")
        $leaf = Split-Path -Path $normalizedRoot -Leaf
        if (-not [string]::IsNullOrWhiteSpace($leaf)) {
          $head.WorkspaceName = $leaf
        }
      }
      $obj.PSObject.Properties.Remove("workspace_roots")
    }
    if ($obj.PSObject.Properties["cursor_version"]) {
      $obj.PSObject.Properties.Remove("cursor_version")
    }
    if ($obj.PSObject.Properties["user_email"]) {
      $obj.PSObject.Properties.Remove("user_email")
    }
    if ($obj.PSObject.Properties["transcript_path"]) {
      $obj.PSObject.Properties.Remove("transcript_path")
    }
    if ($null -ne $obj.prompt -and $obj.prompt -is [string]) {
      $obj.prompt = "..."
    }
    if ($null -ne $obj.text -and $obj.text -is [string]) {
      $obj.text = "..."
    }
    if ($null -ne $obj.content -and $obj.content -is [string]) {
      $obj.content = "..."
    }
    $bodyStr = $obj | ConvertTo-Json -Compress -Depth 20
  } catch {
    $head.IsValidJson = $false
    $bodyStr = $rawInput
    Set-HookFallbackJsonQuotedField $head ConversationId $rawInput -JsonFieldName conversation_id
    Set-HookFallbackJsonQuotedField $head GenerationId $rawInput -JsonFieldName generation_id
    Set-HookFallbackJsonQuotedField $head ModelName $rawInput -JsonFieldName model
    Set-HookFallbackJsonQuotedField $head HookEventName $rawInput -JsonFieldName hook_event_name
    Set-HookFallbackWorkspaceNameFromRoots $head $rawInput
  }

  $bodyStr = [string]$bodyStr
  <# 勿对已是合法 JSON 的 $bodyStr 做全文替换：\n 转义在 "text" 等字段内可被
     (?:\\r\\n|\\n){3,} 误匹配，且替换串 "\n\n" 会写入真实换行符，破坏 JSON，
     导致 afterAgentResponse 等二次 ConvertFrom-Json 失败并报 invalid json。 #>
  return $head, $bodyStr
}

function Get-HookProjectLogPath {
  $projectDir = $env:CURSOR_PROJECT_DIR
  if ([string]::IsNullOrWhiteSpace($projectDir)) {
    $projectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  }
  $dir = Join-Path $projectDir ".cursor/log"
  New-Item -ItemType Directory -Path $dir -Force | Out-Null
  $dateStamp = Get-Date -Format 'yyyy-MM-dd'
  $fileName = "r2e_hook_event_$dateStamp.log"
  return (Join-Path $dir $fileName)
}
<#
  供日志前缀等：典型为 UUID 样式；空白则原样返回，非空白则取第一个 "-" 前的短段。
#>
function Get-PrettyUuid {
  param(
    [Parameter(Mandatory = $false)]
    [AllowEmptyString()]
    [string]$Id
  )
  $s = [string]$Id
  if (-not [string]::IsNullOrWhiteSpace($s)) {
    return ($s -split "-", 2)[0]
  }
  return $s
}
