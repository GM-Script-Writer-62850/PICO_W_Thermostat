"use strict";
function getWeather(){
	function addRow(tbl,name,val){
		if(val=='NA'||val=='')
			return;
		var tr,td;
		tr=make('tr');
		if(name){
			td=make('th');
			insert(td,makeTxt(name));
			insert(tr,td);
		}
		td=make('td');
		if(!name){
			td.setAttribute('colspan',2);
			td.innerHTML=val;
		}
		else
			insert(td,makeTxt(val));
		insert(tr,td);

		insert(tbl,tr);
	}
	var httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				var weather=httpRequest.responseText,
					div=findEle('//div[@id="weather"]',9),
					tbl;
				try{
					weather=JSON.parse(weather);
					findEle('//div[@id="status"]',9).removeAttribute('style');
				}
				catch(e){
					if(!div)
						findEle('//div[@id="status"]',9).setAttribute('style','float:none;-moz-column-count:2;-webkit-column-count:2;column-count:2;padding-left:11%;width:100%;');
					return;
				}
				if(!div){
					div=make('div');
					div.id='weather';
					div.innerHTML='<h3>Current Weather</h3>';
					insert(findEle('//div[@id="body"]',9),div);
				}
				weather=weather.current_observation;
				weather.visibility_string=weather.visibility_mi+' mi ('+weather.visibility_km+' km)';
				weather.pressure_string=(Math.round(weather.pressure_in*.491154*100)/100)+' psi ('+(weather.pressure_mb/10)+' kPa)';
				weather.precip_today_string=weather.precip_today_string==' in ( mm)'?'0 in (0 mm)':weather.precip_today_string;
				tbl=make('table');
				tbl.border=1;
				addRow(tbl,'Condition',weather.weather);
				addRow(tbl,'Temperature',weather.temperature_string);
				if(weather.temperature_string!=weather.feelslike_string)
					addRow(tbl,'Feels Like',weather.feelslike_string);
				addRow(tbl,'Heat index',weather.heat_index_string);
				addRow(tbl,'Wind',weather.wind_string);
				addRow(tbl,'Windchill',weather.windchill_string);
				addRow(tbl,'Dew Point',weather.dewpoint_string);
				addRow(tbl,'Relative Humidity',weather.relative_humidity);
				addRow(tbl,'Air Pressure',weather.pressure_string);
//				addRow(tbl,"Today's Rainfall",weather.precip_today_string);
//				addRow(tbl,'Rainfall/hour',weather.precip_1hr_string);
				addRow(tbl,false,'<a target="_blank" href="'+weather.ob_url+'#forecast">View Forcast Online</a>');
				if(div.childNodes[1])
					div.removeChild(div.childNodes[1]);
				insert(div,tbl);
			}
			else if(httpRequest.status==404){// Unit probally recently booted and weather has not been downloaded
				if(!findEle('//div[@id="weather"]',9))
					findEle('//div[@id="status"]',9).setAttribute('style','float:none;-moz-column-count:2;-webkit-column-count:2;column-count:2;padding-left:11%;width:100%;');
			}
		}
	}
	httpRequest.open('GET', '/tmp/weather.json?noCache'+new Date().getTime());
	httpRequest.send(null);
	setTimeout(getWeather,60000);
}
window.addEventListener("load",getWeather,false);
findEle('//div[@id="status"]',9).className='side';
