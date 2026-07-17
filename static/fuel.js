// =====================================================
// AGIPL FUEL INTELLIGENCE CENTER JS
// =====================================================


let RAW_DATA = {};
let FILTER_DATA = [];

let charts = {};



// =====================================================
// LOAD API DATA
// =====================================================


document.addEventListener(
    "DOMContentLoaded",
    function(){

        fetch("/fuel_data")

        .then(response=>response.json())

        .then(data=>{


            console.log(
                "Fuel API Response",
                data
            );


            if(data.error){

                alert(data.error);

                return;
            }


            RAW_DATA = data;


            FILTER_DATA =
            data.table || [];


            loadSlicers();


            applyFilters();


        })

        .catch(error=>{


            console.error(
                "Fuel API Error",
                error
            );


            alert(
                "Fuel Data Loading Failed"
            );


        });


    }
);





// =====================================================
// LOAD FILTERS
// =====================================================


function loadSlicers(){


    let slicers =
    RAW_DATA.slicers || {};



    fillSelect(
        "dateFilter",
        slicers.dates || []
    );


    fillSelect(
        "siteFilter",
        slicers.sites || []
    );


    fillSelect(
        "categoryFilter",
        slicers.categories || []
    );


    fillSelect(
        "machineFilter",
        slicers.machines || []
    );


    fillSelect(
        "statusFilter",
        slicers.status || []
    );




    document
    .querySelectorAll("select")
    .forEach(select=>{


        select.addEventListener(
            "change",
            applyFilters
        );


    });



}





function fillSelect(id,data){


    let select =
    document.getElementById(id);



    if(!select)
    return;



    data.forEach(value=>{


        let option =
        document.createElement(
            "option"
        );


        option.value=value;

        option.textContent=value;


        select.appendChild(option);



    });



}








// =====================================================
// FILTER ENGINE
// =====================================================


function applyFilters(){


    let date =
    document.getElementById(
        "dateFilter"
    ).value;



    let site =
    document.getElementById(
        "siteFilter"
    ).value;



    let category =
    document.getElementById(
        "categoryFilter"
    ).value;



    let machine =
    document.getElementById(
        "machineFilter"
    ).value;



    let status =
    document.getElementById(
        "statusFilter"
    ).value;




    FILTER_DATA =


    (RAW_DATA.table || [])

    .filter(row=>{


        return (

            date=="ALL" ||
            formatDate(
                row["Working Date"]
            )
            ==
            date

        )

        &&

        (

            site=="ALL" ||
            String(row["Log Book No."])
            ==
            site

        )

        &&

        (

            category=="ALL" ||
            row["Machine Category"]
            ==
            category

        )

        &&

        (

            machine=="ALL" ||
            row["Machine"]
            ==
            machine

        )

        &&

        (

            status=="ALL" ||
            row["Machine Status"]
            ==
            status

        );


    });



    updateDashboard();


}







function formatDate(value){


    if(!value)
    return "";


    return String(value)
    .substring(
        0,
        10
    );


}








// =====================================================
// KPI UPDATE
// =====================================================


function updateDashboard(){



    let fuel =
    sumColumn(
        "Fuel Used"
    );



    let hours =
    sumColumn(
        "Run Hours"
    );



    let machineCount =

    new Set(

        FILTER_DATA.map(
            x=>x["Machine"]
        )

    ).size;



    let avg =

    hours>0

    ?

    (fuel/hours)
    .toFixed(2)

    :

    0;



    let days =

    new Set(

        FILTER_DATA.map(
            x=>x["Working Date"]
        )

    ).size;




    let high =

    FILTER_DATA.filter(

        x=>

        Number(
            x["Fuel Average"]
        )
        >15

    ).length;





    document.getElementById(
        "fuelKpi"
    ).innerHTML =
    formatNumber(fuel)
    +" L";



    document.getElementById(
        "hourKpi"
    ).innerHTML =
    formatNumber(hours);



    document.getElementById(
        "machineKpi"
    ).innerHTML =
    machineCount;



    document.getElementById(
        "avgKpi"
    ).innerHTML =
    avg+" L/Hr";



    document.getElementById(
        "dayKpi"
    ).innerHTML =
    days;



    document.getElementById(
        "highKpi"
    ).innerHTML =
    high;



    renderCharts();


    renderTable();



}





function sumColumn(col){


    return FILTER_DATA.reduce(

        (sum,row)=>

        sum+
        Number(
            row[col] || 0
        ),

        0

    );

}



function formatNumber(num){


    return Number(num)
    .toLocaleString(
        "en-IN",
        {
            maximumFractionDigits:2
        }
    );

}







// =====================================================
// CHART
// =====================================================


function createChart(
    id,
    type,
    labels,
    values
){



    if(charts[id]){

        charts[id].destroy();

    }




    let canvas =
    document.getElementById(id);



    if(!canvas)
    return;



    charts[id] =

    new Chart(
        canvas,
        {

        type:type,


        data:{


            labels:labels,


            datasets:[{

                data:values,


                backgroundColor:
                "#35d5ff"


            }]

        },


        options:{


            responsive:true,


            maintainAspectRatio:false,


            plugins:{


                legend:{
                    display:false
                }

            }


        }


        }

    );

}





// =====================================================
// CHART DATA
// =====================================================


function renderCharts(){


    let daily={};


    FILTER_DATA.forEach(row=>{


        let d =
        formatDate(
            row["Working Date"]
        );


        daily[d]=
        (daily[d]||0)
        +
        Number(
            row["Fuel Used"]||0
        );


    });



    createChart(

        "dailyChart",
        "line",
        Object.keys(daily),
        Object.values(daily)

    );





    groupChart(
        "monthChart",
        "Month"
    );


    groupChart(
        "siteChart",
        "Log Book No."
    );


    groupChart(
        "categoryChart",
        "Machine Category"
    );


    groupChart(
        "machineChart",
        "Machine"
    );


    groupChart(
        "avgChart",
        "Machine",
        "Fuel Average"
    );


}






function groupChart(
id,
column,
value="Fuel Used"
){


    let obj={};



    FILTER_DATA.forEach(row=>{


        let key =
        row[column] || "Unknown";


        obj[key] =

        (obj[key]||0)

        +

        Number(
            row[value]||0
        );


    });



    let data =

    Object.entries(obj)

    .sort(
        (a,b)=>b[1]-a[1]
    )

    .slice(
        0,
        10
    );



    createChart(

        id,

        "bar",

        data.map(
            x=>x[0]
        ),

        data.map(
            x=>x[1]
        )

    );


}







// =====================================================
// TABLE
// =====================================================


function renderTable(){


    let body =
    document.getElementById(
        "fuelTable"
    );


    body.innerHTML="";



    FILTER_DATA.forEach(

        (row,index)=>{


        body.innerHTML +=

        `

        <tr>

        <td>${index+1}</td>

        <td>${row.Month||""}</td>

        <td>${formatDate(row["Working Date"])}</td>

        <td>${row["Log Book No."]||""}</td>

        <td>${row["Machine Category"]||""}</td>

        <td>${row["Machine"]||""}</td>

        <td>${row["RTO Number"]||""}</td>

        <td>${row["Machine Status"]||""}</td>

        <td>${row["Fuel Used"]||0}</td>

        <td>${row["Run Hours"]||0}</td>

        <td>${row["Fuel Average"]||0}</td>

        </tr>

        `;


        }

    );


}
