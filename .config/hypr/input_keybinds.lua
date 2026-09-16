-- ██ ███  ██ █████▄ ██  ██ ██████   ▄████▄ ███  ██ ████▄    ██ ▄█▀ ██████ ██  ██ █████▄ ██ ███  ██ ████▄  ██ ███  ██  ▄████  ▄█████   
-- ██ ██ ▀▄██ ██▄▄█▀ ██  ██   ██     ██▄▄██ ██ ▀▄██ ██  ██   ████   ██▄▄    ▀██▀  ██▄▄██ ██ ██ ▀▄██ ██  ██ ██ ██ ▀▄██ ██  ▄▄▄ ▀▀▀▄▄▄   
-- ██ ██   ██ ██     ▀████▀   ██     ██  ██ ██   ██ ████▀    ██ ▀█▄ ██▄▄▄▄   ██   ██▄▄█▀ ██ ██   ██ ████▀  ██ ██   ██  ▀███▀  █████▀   

hl.config({
    input = {
        kb_layout      = "br,us",
        kb_variant     = "abnt2,intl",
        kb_options     = "grp:win_space_toggle",

        follow_mouse   = 1,
        accel_profile  = "flat",
        force_no_accel = true,
        sensitivity    = 0,

        touchpad = {
            natural_scroll = true,
        },
    },
})

-- MESA DIGITALIZADORA E TOUCHPAD PER-DEVICE
hl.device({
    name          = "pixa3848:00-093a:3848-touchpad",
    sensitivity   = 0,
    accel_profile = "flat",
    scroll_factor = 0.5,
})

hl.device({
    name      = "ugtablet-ugee-s640-pen",
    transform = 0,
    output    = "HDMI-A-2", -- Mudar a tela de acordo com a que vai usar
})

local mainMod = "SUPER"

local terminal = terminal or "kitty"
local fileManager = fileManager or "dolphin"
local menu = menu or "rofi -show drun -theme-str 'window { width: 500px; height: 600px; }'"

-- Binds personalizadas
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd("python3 /$HOME/.config/bin/menu_system.py"))
hl.bind(mainMod .. " + F", hl.dsp.exec_cmd("firefox"))
hl.bind(mainMod .. " + O", hl.dsp.exec_cmd("code"))
hl.bind(mainMod .. " + Z", hl.dsp.exec_cmd("flatpak run com.rtosta.zapzap"))
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("kitty nvim"))

hl.bind(mainMod .. " + W", hl.dsp.exec_cmd("killall waybar && waybar"))
-- Captura de tela (Screenshots)
hl.bind("Print", hl.dsp.exec_cmd("~/.config/bin/screenshot.sh area"))
hl.bind("SHIFT, Print", hl.dsp.exec_cmd("~/.config/bin/screenshot.sh full"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.exec_cmd("~/.config/bin/screenshot.sh edit"))

-- Keybind para desativar/ativar monitor do notebook (WIN + P / WIN + SHIFT + P)
hl.bind(mainMod .. " + P", hl.dsp.exec_cmd('hyprctl keyword monitor "eDP-1,disable"'))
hl.bind(mainMod .. " + SHIFT + P", hl.dsp.exec_cmd('hyprctl keyword monitor "eDP-1, 1920x1080@144, 172x1080, 1.25"'))
hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("hyprlock"))

-- Binds padrão de sistema e janelas
hl.bind(mainMod .. " + Return", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + C", hl.dsp.window.close())
hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + I", hl.dsp.window.pseudo())
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit"))

hl.bind(mainMod .. " + Q", hl.dsp.exec_cmd("kitty"))

-- Movimentação de foco entre janelas
hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- Alternância de workspaces (1 a 10)
for i = 1, 10 do
    local key = i % 10
    hl.bind(mainMod .. " + " .. key,         hl.dsp.focus({ workspace = i }))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

-- Workspace especial (scratchpad magic)
hl.bind(mainMod .. " + S",         hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Rolagem através de workspaces existentes
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Mover / redimensionar janelas arrastando com o mouse
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Teclas multimídia e volume
hl.bind("XF86AudioMute",    hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),   { locked = true, repeating = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("pactl set-source-mute @DEFAULT_SOURCE@ toggle"), { locked = true, repeating = true })

hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("~/.config/bin/volume.sh up"),   { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("~/.config/bin/volume.sh down"), { locked = true, repeating = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("~/.config/bin/volume.sh mute"), { locked = true, repeating = true })

-- Brilho da tela
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("~/.config/bin/brightness.sh up"),   { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("~/.config/bin/brightness.sh down"), { locked = true, repeating = true })

-- Controle de reprodução de mídia (playerctl)
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })

-- Redimensionar janela ativa com o teclado
hl.bind(mainMod .. " + SHIFT + left",  hl.dsp.window.resize({ x = -10, y = 0,  relative = true }), { repeating = true })
hl.bind(mainMod .. " + SHIFT + right", hl.dsp.window.resize({ x = 10,  y = 0,  relative = true }), { repeating = true })
hl.bind(mainMod .. " + SHIFT + up",    hl.dsp.window.resize({ x = 0,   y = -10, relative = true }), { repeating = true })
hl.bind(mainMod .. " + SHIFT + down",  hl.dsp.window.resize({ x = 0,   y = 10,  relative = true }), { repeating = true })
