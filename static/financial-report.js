const period = document.getElementById("id_period");

function updatePeriodControls() {
  const monthly = period.value === "month";
  for (const [name, active] of [["date", !monthly], ["month", monthly]]) {
    const input = document.getElementById("id_" + name);
    document.getElementById(input.id + "_group").hidden = !active;
    input.disabled = !active;
    input.required = active;
  }
}

period.addEventListener("change", updatePeriodControls);
updatePeriodControls();
