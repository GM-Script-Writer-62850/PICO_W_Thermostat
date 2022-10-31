"use strict";
function eventManager(){
	var cnt=make('div'),
		hld=make('div'),
		itm,httpRequest;
	cnt.addEventListener('click',function(e){
		e.stopPropagation();
	},false);

	itm=make('input');
	itm.type='button';
	itm.value='Add Event';
	itm.addEventListener('click',addEvent,false);
	insert(cnt,itm);

	itm=make('input');
	itm.type='button';
	itm.value='Clear Events';
	itm.addEventListener('click',clearEvents,false);
	insert(cnt,itm);

	itm=make('input');
	itm.type='button';
	itm.value='Save Events';
	itm.addEventListener('click',saveEvents,false);
	insert(cnt,itm);

	itm=make('input');
	itm.type='button';
	itm.value='Exit Manager';
	itm.addEventListener('click',function(){
		document.body.removeChild(this.parentNode.parentNode);
	},false);
	insert(cnt,itm);

	itm=make('p');
	insert(itm,makeTxt('The temperature adjustment is applied to the “Target Temperature”. Event changes will NOT be displayed in the temperature preview. Events can not span beyond midnight, for example you can NOT have a event start on Monday @ 23:30 and end on Tuesday @ 0:30, however this can be accomplished by using two separate events where one ends at 23:59 and the other starts at 00:00. The minimum time for a event is one minute. If this is too “complicated” for you to understand the price per question is 30 minutes of cat brushing!'));
	insert(cnt,itm);

	itm=make('div');
	itm.id="events";
	insert(cnt,itm);

	hld.id="overlay";
	hld.addEventListener('click',function(){
		if(confirm('Close Event Manager?\n\t*Unsaved data will be lost!'))
			this.parentNode.removeChild(this);
	},false);
	insert(hld,cnt);
	insert(document.body,hld);

	httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				var cron=JSON.parse(httpRequest.responseText),
					f=thermostat.format.value=="F",
					i,s,x,q,e;
				for(i=0,s=cron.length;i<s;i++){
					e=addEvent();
					findEle('div[@class="ctrl"]/input[@type="checkbox"]',9,e).checked=cron[i]["enable"];
					for(x=0,q=cron[i]["days"].length;x<q;x++){
						findEle('ul//input[@value="'+cron[i]["days"][x]+'"]',9,e).checked=true;
					}
					q=findEle('div/select',6,e);
					for(x=0;x<4;x++)
						q.snapshotItem(x).value=cron[i]["time"][x<2?"start":"end"][x&1?"m":"h"];
					q=cron[i]["offset"];
					if(f){
						q=+(q*1.8).toFixed(5);
						if(Math.round(q)==+q.toFixed(3)){
							q=Math.round(q);
						}
					}
					findEle('div[@class="time"]/input',9,e).value=q;
					findEle('div[@class="ctrl"]/input[@type="text"]',9,e).value=cron[i]["name"];
				}
			}
			else
				alert('A '+httpRequest.status+' error occurred while fetching events!');
		}
	};
	httpRequest.open('GET', 'cron.json?noCache='+new Date().getTime(), true);
	httpRequest.send(null);
}
function validTime(){
	var sel=findEle('select',6,this.parentNode),
		sh=parseInt(sel.snapshotItem(0).value),
		sm=parseInt(sel.snapshotItem(1).value),
		eh=parseInt(sel.snapshotItem(2).value),
		em=parseInt(sel.snapshotItem(3).value);
	if( sh<eh || (sh==eh && sm<em) )
		return this.name=this.value;
	this.value=this.name;
}
function addEvent(){
	var events=findEle('//div[@id="events"]',9),
		evt,btn,i,li,cb,sel,
		ul=make('ul'),
		days=Array('Mon','Tues','Wednes','Thurs','Fri','Satur','Sun');
	for(i=0;i<7;i++){
		li=make('li');
		cb=make('input');
		cb.type='checkbox';
		cb.value=i;
		insert(li,cb);
		insert(li,makeTxt(days[i]+'day'));
		insert(ul,li);
	}
	evt=make('div');
	evt.className='event';
	insert(evt,ul);
	sel=make('select');
	sel.name=0;
	sel.addEventListener('change',validTime,false);
	for(i=0;i<24;i++){
		li=make('option');
		li.value=i;
		li.textContent=i;
		insert(sel,li);
	}
	ul=make('div');
	ul.className='time';
	insert(ul,makeTxt('Start: '));
	insert(ul,sel);
	insert(ul,makeTxt(' : '));
	sel=make('select');
	sel.addEventListener('change',validTime,false);
	sel.name=0;
	for(i=0;i<60;i++){
		li=make('option');
		li.value=i;
		li.textContent=i<10?'0'+i:i;
		insert(sel,li);
	}
	insert(ul,sel);
	insert(ul,make('br'));
	sel=make('select');
	sel.name=0;
	sel.addEventListener('change',validTime,false);
	sel.name=23;
	for(i=0;i<24;i++){
		li=make('option');
		if(i==23)
			li.selected='selected';
		li.value=i;
		li.textContent=i;
		insert(sel,li);
	}
	insert(ul,makeTxt('End: '));
	insert(ul,sel);
	insert(ul,makeTxt(' : '));
	sel=make('select');
	sel.addEventListener('change',validTime,false);
	sel.name=59;
	for(i=0;i<60;i++){
		li=make('option');
		if(i==59)
			li.selected='selected';
		li.value=i;
		li.textContent=i<10?'0'+i:i;
		insert(sel,li);
	}
	insert(ul,sel);
	insert(ul,make('br'));

	li=make('input');
	li.type='text';
	li.value=0;
	li.size=2;
	li.addEventListener('change',function(){this.value=Number(this.value)||0;},false);
	li.setAttribute('onkeydown','return validateKey(this,event,true);');
	insert(ul,makeTxt('Adjust by: '));
	insert(ul,li);
	if(document.thermostat.className!='K')
		insert(ul,makeTxt('°'));
	insert(evt,ul);

	ul=make('div');
	ul.className='ctrl';

	btn=make('input');
	btn.type='text';
	btn.value='Event Name';
	btn.name="name";
	insert(ul,btn);

	btn=make('input');
	btn.type='button';
	btn.value='Delete Event';
	btn.addEventListener('click',function(){
		if(confirm('Delete event "'+this.parentNode.childNodes[0].value+'"'))
			this.parentNode.parentNode.parentNode.removeChild(this.parentNode.parentNode);
	},false);
	insert(ul,btn);

	li=make('input');
	li.type='checkbox';
	li.value='enable';
	li.checked=true;
	insert(ul,makeTxt('Enabled: '));
	btn=make('div');
	insert(ul,li);
	insert(evt,ul);

	insert(events,evt);
	return evt;
}
function clearEvents(){
	findEle('//div[@id="events"]',9).innerHTML='';
}
function saveEvents(){
	var events=findEle('//div[@id="events"]/div',6),
		day,days,ele,i,x,q,s,httpRequest,
		cron=[];
	for(i=0,q=events.snapshotLength;i<q;i++){
		ele=events.snapshotItem(i);
		x=findEle('div/select',6,ele);
		cron[i]={
			"enable":findEle('div[@class="ctrl"]/input[@type="checkbox"]',9,ele).checked,
			"days":[],
			"time":{
				"start":{
					"h":parseInt(x.snapshotItem(0).value),
					"m":parseInt(x.snapshotItem(1).value)
				},
				"end":{
					"h":parseInt(x.snapshotItem(2).value),
					"m":parseInt(x.snapshotItem(3).value)
				}
			},
			"offset":Number(findEle('div[@class="time"]/input',9,ele).value),
			"name":findEle('div[@class="ctrl"]/input[@type="text"]',9,ele).value
		};
		days=findEle('ul//input',6,ele);
		for(x=0,s=days.snapshotLength;x<s;x++){
			day=days.snapshotItem(x);
			if(day.checked)
				cron[i]["days"].push(parseInt(day.value));
		}
	}
	if(thermostat.format.value=="F"){
		for(i in cron){
			cron[i].offset=+(cron[i].offset*(5/9)).toFixed(5);
		}
	}
	httpRequest = new XMLHttpRequest();
	httpRequest.onreadystatechange = function(){
		if(httpRequest.readyState==4){
			if(httpRequest.status==200){
				try{
					JSON.parse(httpRequest.responseText)
					alert('Saved!');
				}
				catch(e){
					alert(httpRequest.responseText);
				}
			}
			else
				alert("A "+httpRequest.status+" error occurred while saving.");
		}
	};
	httpRequest.open('POST', 'cron.php');
	cron=JSON.stringify({"cron":cron});
	httpRequest.setRequestHeader("Content-type", "application/json");
	httpRequest.setRequestHeader("Content-length", cron.length);
	httpRequest.setRequestHeader("Connection", "close");
	httpRequest.send(cron);
}
