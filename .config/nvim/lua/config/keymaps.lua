-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
--

vim.keymap.set("v", "<C-S-Right>", "e", { silent = true })
vim.keymap.set("v", "<C-S-Left>", "b", { silent = true })

vim.g.mapleader = " "

vim.keymap.set("n", "<leader>t", function()
  vim.cmd("belowright 12split")
  vim.cmd("terminal")
  vim.cmd("startinsert")
end, { desc = "Abir terminal" })
