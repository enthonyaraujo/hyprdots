-- ~/.config/nvim/lua/plugins/auto-save.lua
return {
  "Pocco81/auto-save.nvim",
  event = { "InsertLeave", "TextChanged" },
  opts = {
    enabled = true,
    trigger_events = { "InsertLeave", "TextChanged" },
    condition = function(buf)
      local ft = vim.bo[buf].filetype
      return ft ~= "oil" and ft ~= "neo-tree"
    end,
  },
}
