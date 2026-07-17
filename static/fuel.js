// =====================================================
// AGIPL FUEL INTELLIGENCE CENTER JS
// =====================================================


let RAW_DATA = null;

let FILTER_DATA = [];

let charts = {};





// =====================================================
// LOAD DATA
// =====================================================


document.addEventListener(
"DOMContentLoaded",
()=>{

fetch("/fuel_data")

.then(
res=>res.json()
)

.then(
data=>{


RAW_DATA=data;


FILTER_DATA=data.table;


loadSlicers();


applyFilters();


})

.catch(
err=>{

console.log(
"Fuel API Error",
err
);

});


});









// =====================================================
// LOAD SLICERS
// =====================================================


function loadSlicers(){


fillSelect(
"dateFilter",
RAW_DATA.slicers.dates
);


fillSelect(
"siteFilter",
RAW_DATA.slicers.sites
);


fillSelect(
"categoryFilter",
RAW_DATA.slicers.categories
);


fillSelect(
"machineFilter",
RAW_DATA.slicers.machines
);


fillSelect(
"statusFilter",
RAW_DATA.slicers.status
);



document
.querySelectorAll("select")
.forEach(
s=>{

s.addEventListener(
"change",
applyFilters
);

});


}






function fillSelect(id,list){


let select=document.getElementById(id);


list.forEach(
x=>{


let option=document.createElement(
"option"
);


option.value=x;

option.textContent=x;


select.appendChild(option);



});


}








// =====================================================
// FILTER ENGINE
// =====================================================


function applyFilters(){


let date=
document.getElementById(
"dateFilter"
).value;


let site=
document.getElementById(
"siteFilter"
).value;



let category=
document.getElementById(
"categoryFilter"
).value;



let machine=
document.getElementById(
"machineFilter"
).value;



let status=
document.getElementById(
"statusFilter"
).value;




FILTER_DATA =
RAW_DATA.table.filter(
row=>{


return (

(date=="ALL" ||
formatDate(row["Working Date"])==date)

&&

(site=="ALL" ||
row["Log Book No."]==site)

&&

(category=="ALL" ||
row["Machine Category"]==category)

&&

(machine=="ALL" ||
row["Machine"]==machine)

&&

(status=="ALL" ||
row["Machine Status"]==status)


);


});




updateDashboard();


}







function formatDate(d){

if(!d)
return "";


return d.substring(
0,
10
);

}










// =====================================================
// KPI UPDATE
// =====================================================


function updateDashboard(){



let totalFuel =
sum(
"Fuel Used"
);



let totalHours =
sum(
"Run Hours"
);



let machines =
new Set(

FILTER_DATA.map(
x=>x.Machine
)

).size;




let avg =
totalHours>0 ?

(totalFuel/totalHours).toFixed(2)

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
x=>x["Fuel Average"]>=15
).length;



document.getElementById(
"fuelKpi"
).innerHTML =
number(totalFuel)+" L";



document.getElementById(
"hourKpi"
).innerHTML =
number(totalHours);



document.getElementById(
"machineKpi"
).innerHTML =
machines;



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






function sum(col){

return FILTER_DATA.reduce(

(a,b)=>

a+
Number(b[col]||0)

,0

);

}






function number(v){

return Number(v)
.toLocaleString(
"en-IN",
{
maximumFractionDigits:2
}
);

}









// =====================================================
// CHART CREATOR
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



charts[id]=new Chart(

document
.getElementById(id),

{


type:type,


data:{


labels:labels,


datasets:[{


data:values,


backgroundColor:

"#3FD0F2",


borderRadius:6,


borderWidth:1


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


FILTER_DATA.forEach(
r=>{


let d =
formatDate(
r["Working Date"]
);


daily[d]=
(daily[d]||0)
+
Number(r["Fuel Used"]);



});




createChart(

"dailyChart",

"line",

Object.keys(daily),

Object.values(daily)

);







let month={};


FILTER_DATA.forEach(
r=>{


let m=r.Month;


month[m]=
(month[m]||0)
+
Number(r["Fuel Used"]);



});



createChart(

"monthChart",

"bar",

Object.keys(month),

Object.values(month)

);








createGroupChart(

"siteChart",

"Log Book No."

);




createGroupChart(

"categoryChart",

"Machine Category"

);




createGroupChart(

"machineChart",

"Machine"

);





createGroupChart(

"avgChart",

"Machine",

"Fuel Average"

);



}









function createGroupChart(
id,
column,
value="Fuel Used"
){


let obj={};



FILTER_DATA.forEach(
r=>{


let key =
r[column];


obj[key]=

(obj[key]||0)

+

Number(r[value]||0);



});



let sorted =
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

sorted.map(
x=>x[0]
),

sorted.map(
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
