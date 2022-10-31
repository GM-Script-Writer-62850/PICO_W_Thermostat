"use strict";
var temp,TEMP,FORMAT,NEW,OLD,TUBES,RELAYS,NOTICE,CRONOFFSET,SUN,O_CFG,
	convert={
		'C2C':function(C){
			return C;
		},
		'C2F':function(C){
			return C*1.8+32;
		},
		'C2K':function(C){
			return C+273.15;
		},
		'F2C':function(F){
			return (F-32)*5/9;
		},
		'K2C':function(C){
			return C-273.15;
		},
		'2D':function(X,Y){
			return Number(Math.round(X+"e+"+Y)+"e-"+Y);
		}
	},
	CRASH=false,
	config=(function(){
		var c=localStorage.getItem('config');
		if(c===null)
			return {"thermostat":{"noob":true}};
		else
			return JSON.parse(c);
	})();
function findEle(target,i,e){
	target=document.evaluate(target, e?e:document, null, i, null);
	return i==9?target.singleNodeValue:target;
}
function make(e){
	return document.createElement(e);
}
function makeTxt(t){
	return document.createTextNode(t);
}
function insert(h,c){
	h.appendChild(c);
}
function stamp2Time(stamp){
	var h,m,n,
		date=new Date(stamp*1000);
	if(date.getHours()>12){
		h=date.getHours()-12;
		n="PM";
	}
	else{
		h=date.getHours();
		n="AM";
	}
	m=date.getMinutes();
	return h+':'+(m<10?'0'+m:m)+' '+n;
}
function fixFloat(x){
	return Number(x.toFixed(4));
}
function setBackground(e){
	var off,aOff,
		f=e.format.value=='K'?' ':'°',
		t=Number(e.target.value),// target
		t2=Number(e.trigger.value),// trigger
		ee=e.enabled.checked,
		d=Number(e.day.value),
		n=Number(e.night.value),
		a=Number(e.auxon.value)*-1,
		a2=Number(e.auxoff.value),
		ae=e.auxenabled.checked,
		r=Number(e.sunrise.value),
		s=Number(e.sunset.value);
//	if(t+t2+a+a2 > t)
//		a2=e.auxoff.value=0;
	f+=e.format.value;
	document.body.className=t2==0?'copy':(t2<0?'heat':'cool');
	NEW["dayOn"].textContent=ee?fixFloat(t+t2+d)+f:"Off";
	off=fixFloat(t+d);
	NEW["dayOff"].textContent=ee?off+f:"Off";
	NEW["dayAuxOn"].textContent=ae&&ee?fixFloat(t+t2+a+d)+f:"Off";
	aOff=fixFloat(t+t2+a+a2+d);
	NEW["dayAuxOff"].textContent=ae&&ee?(aOff>off?off:aOff)+f:"Off";

	NEW["nightOn"].textContent=ee?fixFloat(t+t2+n)+f:"Off";
	off=fixFloat(t+n);
	NEW["nightOff"].textContent=ee?off+f:"Off";
	NEW["nightAuxOn"].textContent=ae&&ee?fixFloat(t+t2+a+n)+f:"Off";
	aOff=fixFloat(t+t2+a+a2+n);
	NEW["nightAuxOff"].textContent=ae&&ee?(aOff>off?off:aOff)+f:"Off";;
	if(SUN){
		NEW["day"].textContent=stamp2Time(SUN['rise']['stamp']+r*60);
		NEW["night"].textContent=stamp2Time(SUN['set']['stamp']+s*60);
	}
	e.enabled.nextSibling.textContent=ee?'Yes':'No';
	e.auxenabled.nextSibling.textContent=ae?'Yes':'No';
}
function validateKey(ele,e,bool){
	function blur(e){
		e.dispatchEvent(new Event('blur'));
	}
	//console.log(e.key);
	if(bool&&(['_','-'].indexOf(e.key)>-1)&&e.shiftKey&&bool){
		ele.value=ele.value*-1;
		blur(ele);
		return false;
	}
	if('Enter'==e.key){// Enter
		blur(ele);
		return true;
	}
	if(['ArrowUp','w','d','+'].indexOf(e.key)>-1){
		ele.value++;
		blur(ele);
		return false;
	}
	if(['ArrowDown','s','a'].indexOf(e.key)>-1||e.key=='-'&&e.target.selectionStart>0){
		if(bool||ele.value-1>=0){
			ele.value=fixFloat((isNaN(ele.value)?0:ele.value)-1);
			blur(ele);
		}
		return false;
	}
	if(['.','-','Backspace','Delete','Execute','Insert','ArrowLeft','ArrowRight','F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12','Escape','Control','Home','End','PageUp','PageDown'].indexOf(e.key)>-1||!isNaN(e.key)){
		if(!bool&&e.key=='-')
			return false;
		return true;
	}
	// anything else (mostly letters)
	return false;
}
function getSun(){
	var httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				SUN=JSON.parse(httpRequest.responseText);
				setBackground(thermostat);
			//	findEle('//sup[@id="sunrise"]',9).textContent=SUN["rise"]["time"];
			//	findEle('//sup[@id="sunset"]',9).textContent=SUN["set"]["time"];
			}
			if(O_CFG){
				OLD["day"].textContent=stamp2Time(SUN["rise"]["stamp"]+O_CFG["sunrise"]*60);
				OLD["night"].textContent=stamp2Time(SUN["set"]["stamp"]+O_CFG["sunset"]*60);
			}
			setTimeout(getSun,3600000);
		}
	};
	httpRequest.open('GET', 'sun.json?noCache='+new Date().getTime());
	httpRequest.send(null);
}
function getErrorLog(message){
	var httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				try{
					var json=JSON.parse(httpRequest.responseText);
					if(new Date().getTime()/1000 - json.now.stamp > 84600)
						message+="\n\nA unresolved issue has occurred:\nThermostat thinks it is "+json.now.date;
					if(json.error.length>0)
						message+="\n\nA "+(json.time.state?"un":"")+"resolved error has occurred on "+json.time.date+":\n\t"+json.error.join('\n');
					alert(message);
				}
				catch(e){
					console.log(e);
					console.log(httpRequest.responseText);
					alert(message+"\n\n"+"unable to read error cause another error occurred:\n\t"+e)
				}
				setTimeout("CRASH=false",60000);
			}
		}
	};
	httpRequest.open('GET', 'error.json?noCache='+new Date().getTime());
	httpRequest.send(null);
	return true;
}
function updateTemp(){
	var httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				try{
					var json=JSON.parse(httpRequest.responseText),
						f=thermostat.format.value,s;
				}
				catch(e){
					console.log(e);
					console.log(httpRequest.responseText);
					return setTimeout(updateTemp,100);
				}
				TEMP=json.temp;
				temp.textContent=convert['2D'](convert['C2'+f](TEMP),2)+(f=='K'?' ':'°')+f;
				s=json.tube1==0?'Right':'Left';
				TUBES.a.textContent=s;
				TUBES.a.className=s;
				s=json.tube2==0?'Left':'Right';
				TUBES.b.textContent=s;
				TUBES.b.className=s;
				s=json.relay1==0?'Right':'Left';
				RELAYS.a.textContent=s;
				RELAYS.a.className=s;
				s=json.relay2==0?'Left':'Right';
				RELAYS.b.textContent=s;
				RELAYS.b.className=s;
				NOTICE.style.display=json.cycled==2&&json.relay2==1?'block':'none';
				CRONOFFSET.textContent="Current Timed Events are adjusting the temperature by "+(+(json.cron*(thermostat.format.value=="F"?1.8:1)).toFixed(5));
				f=Math.round(Date.now()/1000)-json.age;
				if(f>45&&!CRASH)// 45 seconds
					CRASH=getErrorLog("Temperature data is "+f+" seconds old!\nSomething is wrong");
			}
			setTimeout(updateTemp,9000);
		}
	};
	httpRequest.open('GET', 'temp.json?noCache='+new Date().getTime());
	httpRequest.send(null);
}
function setTarget(e,thermostat){
	var delta={
		"F":thermostat.format.value=='F',
		"AF":1,//1.4616,
		"BF":1,//1.125,
		"ABF":1,//0.8433,
		"AC":0.5,//0.812,
		"BC":0.5,//0.625,
		"ABC":0.5//0.4685
	}
	if(isNaN(e.selectedIndex)){
		e=Number(e.value);
		if(isNaN(e))
			return alert('Numbers only please');
		if(thermostat.trigger.value>0){
			thermostat.target.value=e-((delta.F?delta.AF:delta.AC)/2);
			thermostat.trigger.value=delta.F?delta.AF:delta.AC;
		}
		else{
			thermostat.target.value=e+((delta.F?delta.AF:delta.AC)/2);
			thermostat.trigger.value=-1*(delta.F?delta.AF:delta.AC);
		}
	}
	else{
		thermostat.trigger.value=e.value;
	}
	thermostat.day.value=0;
	thermostat.enabled.checked=true;
	thermostat.auxenabled.checked=true;
	thermostat.auxon.value=delta.F?delta.ABF:delta.ABC;
	thermostat.auxoff.value=thermostat.auxon.value*2;
	setBackground(thermostat);
}
function setNoob(b){
	if(b){
		b=thermostat.trigger.value;
		findEle('//form[@name="thermostat"]//input[not(@name) and (@type="text" or @type="number")]',9).value=Math[b==0?'round':(b>0?'ceil':'floor')](thermostat.target.value);
		findEle('//form[@name="thermostat"]//select[not(@name)]',9).selectedIndex=b==0?2:(b>0?1:0);
		b=true;
	}
	findEle('//div[@id="body"]',9).className=b?'noob':'';
	config.thermostat.noob=b;
	localStorage.setItem('config',JSON.stringify(config));
}
function apply(e){
	var msg=' setting is within the margin of error, this can cause poor efficiency\nClick OK to ignore';
	if(Math.abs(e.trigger.value)<=(thermostat.format.value=="F"?1.197:0.665)&&e.trigger.value!=0&&e.skill.value=='adv'){
		if(!confirm('Your "'+(e.trigger.value>0?'Cool':'Heat')+'"'+msg))
			return false;
	}
	if(e.auxoff.value<=(thermostat.format.value=="F"?0.9:0.5)){
		if(!confirm('Your "Auxiliary Off"'+msg))
			return false;
	}
	if(e.enabled.checked==true){
		if(!e.auxenabled.checked && e.trigger.value<0){
			if(!confirm('Warning: Aux Heating is disabled!\nIs this OK?'))
				e.auxenabled.checked=true;
		}
	}
	else{
		if(!confirm('Warning: The System is disabled!\nIs this OK?'))
			e.enabled.checked=true;
	}
	var inpts=findEle('.//input[(@type="text" or @type="number") and @name]',6,thermostat),
		inpt,httpRequest,i,
		data={};
	for(i=inpts.snapshotLength-1;i>-1;i--){
		inpt=inpts.snapshotItem(i);
		data[inpt.name]=Number(inpt.value)||inpt.value;
		// Convert data input to Celsius
		if(thermostat.format.value=="F" && inpt.nextElementSibling){
			if(inpt.nextElementSibling.className=="deg"){
				if(inpt.name=="target"){
					data.target=+(data.target-32)*(5/9).toFixed(5);
				}
				else{
					data[inpt.name]=+(data[inpt.name]*(5/9)).toFixed(5);
				}
			}
		}
		else if(thermostat.format.value=="K" && inpt.name=="target"){
			data[inpt.name]-=273.15;
		}
	}
	inpts=findEle('.//input[@type="checkbox"]',6,thermostat);
	for(i=inpts.snapshotLength-1;i>-1;i--){
		inpt=inpts.snapshotItem(i);
		data[inpt.name]=inpt.checked?1:0;
	}
	data['format']=thermostat.format.value;
	data=JSON.stringify(data);
	httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				try{
					O_CFG=JSON.parse(httpRequest.responseText);
					restore(O_CFG);
					alert("Settings Applied!");
					for (i in NEW)
						OLD[i].textContent=NEW[i].textContent;
					findEle('//div[@id="oldSettings"]',9).className=O_CFG["trigger"]==0?'copy':(O_CFG["trigger"]>0?'cool':'heat');
				}
				catch(e){
					alert("Something went wrong:\n"+httpRequest.responseText);
				}
			}
			else
				alert('Error: '+httpRequest.status)
		}
	};
	httpRequest.open('POST', 'apply.php');
	httpRequest.setRequestHeader("Content-type", "application/json");
	httpRequest.setRequestHeader("Content-Length", data.length);
	httpRequest.send(data);
	return false;
}
function restore(O_CFG){
	var i,x,ele;
	for(i in O_CFG){
		ele=thermostat[i]
		if(ele.type=='checkbox')
			ele.checked=O_CFG[i]==1;
		else{
			ele.value=O_CFG[i];
			// Convert data from Celsius
			if(O_CFG.format=="F" && ele.nextElementSibling){
				if(ele.nextElementSibling.className=="deg"){
					if(i=="target"){
						x=+(32+(O_CFG.target*1.8)).toFixed(5);
						console.log(i,'=',x);
						if(Math.round(x*100)/100==+x.toFixed(3)){
							x=+x.toFixed(3);
						}
					}
					else{
						x=+(O_CFG[i]*1.8).toFixed(5);
						console.log(i,'=',x);
						if(Math.round(x)==+x.toFixed(3))
							x=Math.round(x);
					}
					console.log(i,'=',x);
					ele.value=x;
				}
			}
			else if(O_CFG.format=="K" && i=="target"){
				ele.value=O_CFG[i]+273.15;
			}
		}
	}
	if(config.thermostat.noob)
		setNoob(true);
	setBackground(thermostat);
}
function load(){
	thermostat.format.addEventListener('change',function(){
		if(thermostat.className=='F'||this.value=='F'){
			var x=[thermostat.auxoff,thermostat.auxon],i;
			for(i in x){
				if(x[i].disabled)
					x[i].value=(this.value=='F'?x[i].value*9/5:x[i].value*5/9);
			}
		}
		FORMAT=this.value;
		thermostat.className=FORMAT;
		setBackground(thermostat);
	},false);
	var eles,httpRequest;
	temp=document.getElementById("temp");
	eles=findEle('//table[@id="newSettings"]//td',6);
	NEW={
		"day":eles.snapshotItem(0),
		"dayOn":eles.snapshotItem(1),
		"dayOff":eles.snapshotItem(2),
		"dayAuxOn":eles.snapshotItem(3),
		"dayAuxOff":eles.snapshotItem(4),
		"night":eles.snapshotItem(5),
		"nightOn":eles.snapshotItem(6),
		"nightOff":eles.snapshotItem(7),
		"nightAuxOn":eles.snapshotItem(8),
		"nightAuxOff":eles.snapshotItem(9)
	}
	eles=findEle('//div[@id="oldSettings"]/table//td',6);
	OLD={
		"day":eles.snapshotItem(0),
		"dayOn":eles.snapshotItem(1),
		"dayOff":eles.snapshotItem(2),
		"dayAuxOn":eles.snapshotItem(3),
		"dayAuxOff":eles.snapshotItem(4),
		"night":eles.snapshotItem(5),
		"nightOn":eles.snapshotItem(6),
		"nightOff":eles.snapshotItem(7),
		"nightAuxOn":eles.snapshotItem(8),
		"nightAuxOff":eles.snapshotItem(9)
	}
	eles=findEle('//div[@id="tubes"]/table//td/span',6);
	TUBES={
		"a":eles.snapshotItem(0),
		"b":eles.snapshotItem(1)
	}
	eles=findEle('//div[@id="relays"]/table//td/span',6)
	RELAYS={
		"a":eles.snapshotItem(0),
		"b":eles.snapshotItem(1)
	}
	NOTICE=findEle('//div[@id="notice"]',9);
	CRONOFFSET=findEle('//div[@id="cron_status"]/span',9);
	updateTemp();
	getSun(true);
	setBackground(thermostat);
	if(config.thermostat.noob)
		findEle('//div[@id="body"]',9).className='noob';
	else
		thermostat.skill.selectedIndex=1;
	httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				var i;
				O_CFG=JSON.parse(httpRequest.responseText);
				thermostat.className=O_CFG.format;
				restore(O_CFG);
				for (i in NEW)
					OLD[i].textContent=NEW[i].textContent;
				findEle('//div[@id="oldSettings"]',9).className=O_CFG["trigger"]==0?'copy':(O_CFG["trigger"]>0?'cool':'heat');
			}
			else
				alert('A '+httpRequest.status+' error occurred while trying to load the current settings.\nPlease press F5 on the keyboard.');
		}
	};
	httpRequest.open('GET', 'config.json?noCache='+new Date().getTime());
	httpRequest.send(null);
}
