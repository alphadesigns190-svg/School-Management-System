document.addEventListener("click", (e) => {
  const target = e.target;
  if (!(target instanceof HTMLElement)) return;
  if (!target.classList.contains("js-confirm")) return;

  const message = target.getAttribute("data-confirm") || "Are you sure?";
  if (!window.confirm(message)) {
    e.preventDefault();
  }
});

function debounce(fn, waitMs) {
  let t = null;
  return (...args) => {
    if (t) window.clearTimeout(t);
    t = window.setTimeout(() => fn(...args), waitMs);
  };
}

function formatAfn(value) {
  const n = Number(value ?? 0);
  if (!Number.isFinite(n)) return `؋\u00A0\u00A0${value ?? 0}`;
  return `؋\u00A0\u00A0${Math.round(n).toLocaleString()}`;
}

async function updateStudentsTable(searchValue) {
  const table = document.getElementById("students-table");
  if (!(table instanceof HTMLTableElement)) return;

  const tbody = table.querySelector("tbody");
  if (!tbody) return;

  const fields = JSON.parse(table.dataset.fields || "[]");
  const idField = table.dataset.idField || "id";

  if (!searchValue) {
    // If empty, just reload the page to show the normal full list.
    window.location.href = "/students";
    return;
  }

  const res = await fetch(`/students/_data?q=${encodeURIComponent(searchValue)}`, {
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) return;
  const data = await res.json();
  const students = Array.isArray(data.students) ? data.students : [];

  tbody.innerHTML = "";
  if (students.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.className = "muted";
    td.colSpan = fields.length + 1;
    td.textContent = "No students found.";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  for (const s of students) {
    const tr = document.createElement("tr");
    for (const name of fields) {
      const td = document.createElement("td");
      td.textContent = s?.[name] ?? "";
      tr.appendChild(td);
    }

    const tdActions = document.createElement("td");
    tdActions.className = "td-actions";
    const sid = s?.[idField];
    if (sid) {
      const edit = document.createElement("a");
      edit.className = "link";
      edit.href = `/students/${encodeURIComponent(String(sid))}/edit`;
      edit.textContent = "Edit";

      const report = document.createElement("a");
      report.className = "link";
      report.href = `/reports/student/${encodeURIComponent(String(sid))}`;
      report.textContent = "Report";

      const form = document.createElement("form");
      form.method = "post";
      form.action = `/students/${encodeURIComponent(String(sid))}/delete`;
      form.className = "inline";

      const del = document.createElement("button");
      del.type = "submit";
      del.className = "link danger js-confirm";
      del.setAttribute("data-confirm", "Delete this student?");
      del.textContent = "Delete";

      form.appendChild(del);
      tdActions.appendChild(edit);
      tdActions.appendChild(document.createTextNode(" "));
      tdActions.appendChild(report);
      tdActions.appendChild(document.createTextNode(" "));
      tdActions.appendChild(form);
    }

    tr.appendChild(tdActions);
    tbody.appendChild(tr);
  }
}

function setupStudentsTopSearch() {
  if (!window.location.pathname.startsWith("/students")) return;
  const input = document.querySelector('input.js-global-search[name="q"]');
  if (!(input instanceof HTMLInputElement)) return;

  const handler = debounce(() => {
    const q = input.value.trim();
    const url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q);
    else url.searchParams.delete("q");
    window.history.replaceState({}, "", url.toString());
    updateStudentsTable(q);
  }, 250);

  input.addEventListener("input", handler);

  const form = input.closest("form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      handler();
    });
  }
}

async function updateTeachersTable(searchValue) {
  const table = document.getElementById("teachers-table");
  if (!(table instanceof HTMLTableElement)) return;
  const tbody = table.querySelector("tbody");
  if (!tbody) return;

  const fields = JSON.parse(table.dataset.fields || "[]");
  const idField = table.dataset.idField || "id";

  if (!searchValue) {
    window.location.href = "/teachers";
    return;
  }

  const res = await fetch(`/teachers/_data?q=${encodeURIComponent(searchValue)}`, {
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) return;
  const data = await res.json();
  const teachers = Array.isArray(data.teachers) ? data.teachers : [];

  tbody.innerHTML = "";
  if (teachers.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.className = "muted";
    td.colSpan = fields.length + 1;
    td.textContent = "No teachers found.";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  for (const t of teachers) {
    const tr = document.createElement("tr");
    for (const name of fields) {
      const td = document.createElement("td");
      if (name === "salary") td.textContent = formatAfn(t?.[name] ?? 0);
      else td.textContent = t?.[name] ?? "";
      tr.appendChild(td);
    }

    const tdActions = document.createElement("td");
    tdActions.className = "td-actions";
    const tid = t?.[idField];
    if (tid) {
      const edit = document.createElement("a");
      edit.className = "link";
      edit.href = `/teachers/${encodeURIComponent(String(tid))}/edit`;
      edit.textContent = "Edit";

      const form = document.createElement("form");
      form.method = "post";
      form.action = `/teachers/${encodeURIComponent(String(tid))}/delete`;
      form.className = "inline";

      const del = document.createElement("button");
      del.type = "submit";
      del.className = "link danger js-confirm";
      del.setAttribute("data-confirm", "Delete this teacher?");
      del.textContent = "Delete";

      form.appendChild(del);
      tdActions.appendChild(edit);
      tdActions.appendChild(document.createTextNode(" "));
      tdActions.appendChild(form);
    }

    tr.appendChild(tdActions);
    tbody.appendChild(tr);
  }
}

function setupTeachersTopSearch() {
  if (!window.location.pathname.startsWith("/teachers")) return;
  const input = document.querySelector('input.js-global-search[name="q"]');
  if (!(input instanceof HTMLInputElement)) return;

  const handler = debounce(() => {
    const q = input.value.trim();
    const url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q);
    else url.searchParams.delete("q");
    window.history.replaceState({}, "", url.toString());
    updateTeachersTable(q);
  }, 250);

  input.addEventListener("input", handler);
  const form = input.closest("form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      handler();
    });
  }
}

async function updateCoursesTable(searchValue) {
  const table = document.getElementById("courses-table");
  if (!(table instanceof HTMLTableElement)) return;
  const tbody = table.querySelector("tbody");
  if (!tbody) return;

  if (!searchValue) {
    window.location.href = "/courses";
    return;
  }

  const res = await fetch(`/courses/_data?q=${encodeURIComponent(searchValue)}`, {
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) return;
  const data = await res.json();
  const courses = Array.isArray(data.courses) ? data.courses : [];

  tbody.innerHTML = "";
  if (courses.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.className = "muted";
    td.colSpan = 8;
    td.textContent = "No courses found.";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  for (const c of courses) {
    const tr = document.createElement("tr");

    const cells = [
      c?.id ?? "",
      c?.course_name ?? "",
      formatAfn(c?.fee ?? 0),
      c?.duration ?? "",
      c?.shift ?? "",
      c?.teacher_name ? `${c.teacher_name} (${c.teacher_id ?? ""})` : "—",
      c?.student_count ?? 0,
    ];
    for (const text of cells) {
      const td = document.createElement("td");
      td.textContent = String(text);
      if (text === "—") td.className = "muted";
      tr.appendChild(td);
    }

    const tdActions = document.createElement("td");
    tdActions.className = "td-actions";
    const cid = c?.id;
    if (cid) {
      const edit = document.createElement("a");
      edit.className = "link";
      edit.href = `/courses/${encodeURIComponent(String(cid))}/edit`;
      edit.textContent = "Edit";

      const form = document.createElement("form");
      form.method = "post";
      form.action = `/courses/${encodeURIComponent(String(cid))}/delete`;
      form.className = "inline";

      const del = document.createElement("button");
      del.type = "submit";
      del.className = "link danger js-confirm";
      del.setAttribute("data-confirm", "Delete this course?");
      del.textContent = "Delete";

      form.appendChild(del);
      tdActions.appendChild(edit);
      tdActions.appendChild(document.createTextNode(" "));
      tdActions.appendChild(form);
    }

    tr.appendChild(tdActions);
    tbody.appendChild(tr);
  }
}

function setupCoursesTopSearch() {
  if (!window.location.pathname.startsWith("/courses")) return;
  const input = document.querySelector('input.js-global-search[name="q"]');
  if (!(input instanceof HTMLInputElement)) return;

  const handler = debounce(() => {
    const q = input.value.trim();
    const url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q);
    else url.searchParams.delete("q");
    window.history.replaceState({}, "", url.toString());
    updateCoursesTable(q);
  }, 250);

  input.addEventListener("input", handler);
  const form = input.closest("form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      handler();
    });
  }
}

async function updatePaymentStudentPreview(studentId) {
  const nameEl = document.getElementById("payment-student-name");
  const fatherEl = document.getElementById("payment-student-father");
  const courseEl = document.getElementById("payment-student-course");
  const shiftEl = document.getElementById("payment-student-shift");
  const idEl = document.getElementById("payment-student-id");
  const totalFeeEl = document.getElementById("payment-total-fee");
  const totalPaidEl = document.getElementById("payment-total-paid");
  const remainingEl = document.getElementById("payment-remaining-balance");
  if (!nameEl || !fatherEl || !courseEl || !shiftEl || !totalFeeEl || !totalPaidEl || !remainingEl) return;

  const clearPreview = () => {
    if (idEl) idEl.textContent = "-";
    nameEl.textContent = "-";
    fatherEl.textContent = "-";
    courseEl.textContent = "-";
    shiftEl.textContent = "-";
    totalFeeEl.textContent = "-";
    totalPaidEl.textContent = "-";
    remainingEl.textContent = "-";
  };

  const digits = (studentId || "").trim().replace(/\D/g, "");
  const id = digits ? `ST-${digits.padStart(3, "0")}` : "";
  if (!id) {
    clearPreview();
    return;
  }

  const res = await fetch(`/payments/student-info/${encodeURIComponent(id)}`, {
    headers: { "Accept": "application/json" },
  });
  if (!res.ok) {
    clearPreview();
    return;
  }

  const data = await res.json();
  if (!data || !data.found || !data.student) {
    clearPreview();
    nameEl.textContent = "Student not found";
    return;
  }

  const student = data.student;
  if (idEl) idEl.textContent = student.id || id;
  nameEl.textContent = student.name || "-";
  fatherEl.textContent = student.father_name || "-";
  courseEl.textContent = student.course_name ? `${student.course_name} (${student.course_id || "-"})` : "No course assigned";
  shiftEl.textContent = student.shift || "-";
  totalFeeEl.textContent = formatAfn(student.total_fee ?? 0);
  totalPaidEl.textContent = formatAfn(student.total_paid ?? 0);
  remainingEl.textContent = formatAfn(student.remaining_balance ?? 0);
}

function setupPaymentLookup() {
  if (!window.location.pathname.startsWith("/payments")) return;
  const input = document.querySelector(".js-payment-student-number");
  if (!(input instanceof HTMLInputElement)) return;
  const hidden = document.querySelector(".js-payment-student-id-hidden");
  if (!(hidden instanceof HTMLInputElement)) return;

  const handler = debounce(() => {
    const digits = input.value.replace(/\D/g, "").slice(0, 3);
    input.value = digits;
    hidden.value = digits ? `ST-${digits.padStart(3, "0")}` : "";
    updatePaymentStudentPreview(input.value);
  }, 250);

  input.addEventListener("input", handler);
  input.addEventListener("blur", handler);
  handler();
}

async function updateEnrollmentStudentPreview(studentNumber) {
  const idEl = document.getElementById("enrollment-student-id");
  const nameEl = document.getElementById("enrollment-student-name");
  const fatherEl = document.getElementById("enrollment-student-father");
  const phoneEl = document.getElementById("enrollment-student-phone");
  const statusEl = document.getElementById("enrollment-student-status");
  const courseEl = document.getElementById("enrollment-student-course");
  if (!idEl || !nameEl || !fatherEl || !phoneEl || !statusEl || !courseEl) return;

  const clearPreview = () => {
    idEl.textContent = "-";
    nameEl.textContent = "-";
    fatherEl.textContent = "-";
    phoneEl.textContent = "-";
    statusEl.textContent = "-";
    courseEl.textContent = "-";
  };

  const digits = (studentNumber || "").trim().replace(/\D/g, "");
  const studentId = digits ? `ST-${digits.padStart(3, "0")}` : "";
  if (!studentId) {
    clearPreview();
    return;
  }

  const res = await fetch(`/enrollments/student-info/${encodeURIComponent(studentId)}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    clearPreview();
    return;
  }

  const data = await res.json();
  if (!data || !data.found || !data.student) {
    clearPreview();
    nameEl.textContent = "Student not found";
    return;
  }

  const student = data.student;
  idEl.textContent = student.id || studentId;
  nameEl.textContent = student.name || "-";
  fatherEl.textContent = student.father_name || "-";
  phoneEl.textContent = student.phone || "-";
  statusEl.textContent = student.status || "-";
  courseEl.textContent = student.course_name ? `${student.course_name} (${student.course_id || "-"})` : "No course assigned";
}

function setupEnrollmentLookup() {
  if (!window.location.pathname.startsWith("/enrollments")) return;
  const input = document.querySelector(".js-enrollment-student-number");
  if (!(input instanceof HTMLInputElement)) return;
  const hidden = document.querySelector(".js-enrollment-student-id-hidden");
  if (!(hidden instanceof HTMLInputElement)) return;

  const handler = debounce(() => {
    const digits = input.value.replace(/\D/g, "").slice(0, 3);
    input.value = digits;
    hidden.value = digits ? `ST-${digits.padStart(3, "0")}` : "";
    updateEnrollmentStudentPreview(input.value);
  }, 250);

  input.addEventListener("input", handler);
  input.addEventListener("blur", handler);
  handler();
}

function setupDropdownPolish() {
  const dropdowns = Array.from(document.querySelectorAll("details.menu-dropdown"));
  if (dropdowns.length === 0) return;

  dropdowns.forEach((dropdown) => {
    dropdown.addEventListener("toggle", () => {
      if (!dropdown.open) return;
      dropdowns.forEach((other) => {
        if (other !== dropdown) other.open = false;
      });
    });
  });

  document.addEventListener("click", (e) => {
    const target = e.target;
    if (!(target instanceof Node)) return;
    dropdowns.forEach((dropdown) => {
      if (!dropdown.contains(target)) dropdown.open = false;
    });
  });
}

function gradeFromTotal(total) {
  if (total >= 90) return "A";
  if (total >= 80) return "B";
  if (total >= 70) return "C";
  if (total >= 60) return "D";
  return "F";
}

function calcResultForm() {
  const markInputs = Array.from(document.querySelectorAll("input.js-mark"));
  if (markInputs.length === 0) return;

  const totalInput = document.querySelector('input[name="total_marks"]');
  const gradeInput = document.querySelector('input[name="grade"]');
  if (!totalInput || !gradeInput) return;

  const total = markInputs.reduce((sum, el) => {
    const v = (el.value || "").trim();
    const n = v === "" ? 0 : parseInt(v, 10);
    return sum + (Number.isFinite(n) ? n : 0);
  }, 0);

  totalInput.value = String(total);
  gradeInput.value = gradeFromTotal(total);
}

document.addEventListener("input", (e) => {
  const target = e.target;
  if (!(target instanceof HTMLElement)) return;
  if (!target.classList.contains("js-mark")) return;
  calcResultForm();
});

document.addEventListener("DOMContentLoaded", () => {
  setupStudentsTopSearch();
  setupTeachersTopSearch();
  setupCoursesTopSearch();
  setupPaymentLookup();
  setupEnrollmentLookup();
  setupDropdownPolish();
  calcResultForm();
});
