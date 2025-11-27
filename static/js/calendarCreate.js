document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("calendarCreateForm");
  const yearSelect = document.getElementById("year");

  // Populate years dynamically
  for (let y = 2025; y <= 2035; y++) {
    yearSelect.innerHTML += `<option value="${y}">${y}</option>`;
  }

  form.addEventListener("submit", async function(event) {
    event.preventDefault(); // prevent page reload

    const month = document.getElementById("month").value;
    const year = document.getElementById("year").value;
    const name = document.getElementById("name").value;

     //creates payload to saved to DB
    const payload = {month:month,year:year,name:name};
    //test line to see if calendar html loads the corract grid. delete once we know it works
    //this line should be on the bottom try catch block to then test with DB
    window.location.href=`calendar.html?month=${month}&year=${year}&name=${encodeURIComponent(name)}`;
  });

    //saves or fails to save on DB
    try{
        const response =  fetch("OUR DB CALL",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify(payload)
        })

        const result = response.json();
        console.log("Calendar created successfully:", result);

        //redirects to calendar view page once it is saved 
         window.location.href=`calendar.html?month=${month}&year=${year}`;

        if (!response.ok){{
            throw new Error("Failed to create calendar");
        }
    } 
    } catch(err){
        console.error("Error creating calendar:", err);
        alert("There was an error creating your calendar. Please try again.");
    }

});