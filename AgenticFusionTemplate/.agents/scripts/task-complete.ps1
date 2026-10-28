# Plays a short completion tone for the Codex and Claude Code Stop hooks.
# Ignore audio failures so a missing device never blocks the agent's response.
try {
    $rate = 22050
    $count = [int]($rate * 0.24)
    $stream = [System.IO.MemoryStream]::new()
    $writer = [System.IO.BinaryWriter]::new($stream)
    $ascii = [System.Text.Encoding]::ASCII
    $writer.Write($ascii.GetBytes('RIFF'))
    $writer.Write([int](36 + 2 * $count))
    $writer.Write($ascii.GetBytes('WAVEfmt '))
    $writer.Write([int]16)
    $writer.Write([int16]1)
    $writer.Write([int16]1)
    $writer.Write([int]$rate)
    $writer.Write([int](2 * $rate))
    $writer.Write([int16]2)
    $writer.Write([int16]16)
    $writer.Write($ascii.GetBytes('data'))
    $writer.Write([int](2 * $count))
    for ($i = 0; $i -lt $count; $i++) {
        $fade = [Math]::Min(1.0, [Math]::Min($i / 250.0, ($count - $i) / 500.0))
        $sample = [int16][Math]::Round(9000 * $fade * [Math]::Sin(2 * [Math]::PI * 880 * $i / $rate))
        $writer.Write($sample)
    }
    $writer.Flush()
    $stream.Position = 0
    $player = [System.Media.SoundPlayer]::new($stream)
    $player.PlaySync()
}
catch {
    try { [System.Media.SystemSounds]::Asterisk.Play(); Start-Sleep -Milliseconds 300 } catch {}
}
finally {
    if ($player) { $player.Dispose() }
    if ($writer) { $writer.Dispose() }
    if ($stream) { $stream.Dispose() }
}
