// Feature content uses simple Markdown tables with a header and separator row.
/** @param {string} markdown @returns {string[][]} */
export function tableRows(markdown) {
  return markdown.split('\n').filter(line => line.startsWith('|') && !/^[| :\-]+$/.test(line))
    .slice(1).map(line => line.split('|').slice(1, -1).map(cell => cell.trim()));
}
