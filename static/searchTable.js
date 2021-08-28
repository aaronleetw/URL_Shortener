function searchInTable(num, mode) {
    var input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("searchInput" + num);
    filter = input.value.toUpperCase();
    table = document.getElementById("table");
    tr = table.getElementsByClassName("row");
    startwith = 1
    if (mode == "bulk") startwith = 0

    for (i = startwith; i < tr.length; i++) {
        td = tr[i].getElementsByClassName("col")[num];
        console.log(td.innerHTML)
        if (td) {
            txtValue = ""
            if (mode == "manage") {
                txtValue = td.textContent || td.innerText;
            } else if (mode == "bulk") {
                txtValue = td.getElementsByTagName("input")[0].value;
                console.log(txtValue)
            }
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}