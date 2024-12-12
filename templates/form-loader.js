document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("dynamic-form-container");

    // Lade die Felder von der API
    const response = await fetch("/dynamic_form_fields");
    const { fields } = await response.json();

    // Generiere das Formular
    const form = document.createElement("form");
    form.method = "post";
    form.action = "/login/formular/submit/";

    fields.forEach(field => {
        const label = document.createElement("label");
        label.textContent = field.name.replace(/_/g, " ").toUpperCase();
        form.appendChild(label);

        let input;
        if (field.type === "textarea") {
            input = document.createElement("textarea");
        } else {
            input = document.createElement("input");
            input.type = field.type;
        }

        input.name = field.name;
        input.required = field.required || false;
        form.appendChild(input);
    });

    const submitButton = document.createElement("input");
    submitButton.type = "submit";
    submitButton.value = "Submit";
    form.appendChild(submitButton);

    container.appendChild(form);
});
