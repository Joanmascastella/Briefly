function filterTable() {
  const input = document.getElementById("searchInput");
  const filter = input.value.toLowerCase();
  const table = document.getElementById("userTable");
  const tr = table.getElementsByTagName("tr");

  // Loop through all table rows, skipping the table header row (index 0).
  for (let i = 1; i < tr.length; i++) {
    const td = tr[i].getElementsByTagName("td")[0]; // "Full Name" cell is first column
    if (td) {
      const txtValue = td.textContent || td.innerText;
      // Show row if the text matches, else hide it
      if (txtValue.toLowerCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}