<?php
$file='data/thermostat.json';
$log='data/thermostat.txt';
if(isset($_GET['firstboot'])){
	if(file_exists($file)){
		set_time_limit(0);
		ob_start();
		header('Content-type: text/plain');
		header("Content-Encoding: none");
		echo "OK";
		header('Content-Length: '.ob_get_length());
		header('Connection: close');
		ob_end_flush();
		@ob_flush();
		flush();
		if(session_id()) session_write_close();
		//fastcgi_finish_request();
		$file=file_get_contents($file);
		$file=json_decode($file);
		$file->{"noexport"}=time();
		$file=json_encode($file);
		$options = array(
			'http' => array(
				'header'  => array(
					"Content-type: application/json",
					"Content-Length: ".strlen($file)
				),
				'method'  => 'POST',
				'content' => $file
			)
		);
		$options=stream_context_create($options);
		sleep(1);
		@file_get_contents("http://".$_SERVER['REMOTE_ADDR']."/apply.php", false, $options);
		die("Client can't read this as the connection was closed a while ago");
	}
	else{
		header('Content-type: text/plain', true);
		echo "NO FILE";
	}
}
else{
	$json = file_get_contents('php://input');
	if($json!=''){
		header('Content-type: text/plain', true);
		$json = json_decode($json);
		if(is_array($json)){
			// log(s)
			if (filesize($log)>41943040){// 5 Mebibyte
				if(file_exists("$file.4"))
					unlink("$file.4");
				if(file_exists("$file.3"))
					rename("$file.3","$file.4");
				if(file_exists("$file.2"))
					rename("$file.2","$file.3");
				if(file_exists("$file.1"))
					rename("$file.1","$file.2");
				rename($file,"$file.1");
			}
			$file=fopen($log,'a');
			foreach($json as $row){
				$row=$row->{"time"}." ".
					$row->{"mode"}." ".
					$row->{"temp"}." ".
					$row->{"relays"}[0]." ".
					$row->{"relays"}[1]." ".
					#$row->{"tubes"}[0]." ".
					#$row->{"tubes"}[1]." ".
					$row->{"saved"}."\n";
				fwrite($file,$row);
			}
			fclose($file);
		}
		else{
			// config
			if (file_exists($file))
				$cfg=json_decode(file_get_contents($file));
			else
				$cfg=(object)array();
			foreach($json as $key => $val){
				$cfg->{$key}=$val;
			}
			$file=fopen($file,"w");
			if(fwrite($file,json_encode($cfg))===FALSE)
				echo "Unable to write file.";
			fclose($file);
		}
		echo "OK";
	}
	else if(file_exists($log)){
		// view log
		if(isset($_GET['page']) && is_numeric($_GET['page'])){
			$file=intval($_GET['page']);
			if($file == 0){
				$file=$log;
				$page=1;
			}
			else if (file_exists($log.'.'.$file)){
				$page=$file;
				$file=$log.'.'.$file;
			}
			else
				$file=$log;
			$file=file_get_contents($file);
			$rows=array_reverse(explode("\n",$file));
		}
		else{
			$file=file_get_contents($log);
			$rows=array_reverse(explode("\n",$file));
			if(file_exists("$log.1") && filesize($log)<8388608){// 1 Mebibyte
				$file=file_get_contents("$log.1");
				$rows=array_merge($rows,array_reverse(explode("\n",$file)));
				$page=-1;
			}
			else
				$page=1;
		}
		$set=0;
		$time=0;
		echo '<!DOCTYPE html>'.
			'<html>'.
			'	<head>'.
			'		<meta charset="UTF-8"/>'.
			'		<!--<meta name="ROBOTS" content="NOINDEX, NOFOLLOW"/>-->'.
			'		<title>Thermostat Activity Log</title>'.
			'		<link href="style/images/favicon.png" rel="shortcut icon">'.
			'		<style type="text/css">'.
			'			body{'.
			'				font-family:DejaVu Serif;'.
			'				background:#383838;'.
			'				color:white;'.
			'				text-align:center;'.
			'			}'.
			'			a{'.
			'				color:lightblue;'.
			'			}'.
			'			td{'.
			'				text-align:left;'.
			'				font-family:monospace;'.
			'			}'.
			'			table{'.
			'				margin-left:auto;'.
			'				margin-right:auto;'.
			'			}'.
			'			.temp > span{'.
			'				display:none;'.
			'			}'.
			'			body.C .temp > .C,'.
			'			body.F .temp > .F,'.
			'			body.K .temp > .K{'.
			'				display:inline;'.
			'			}'.
			'			.date{'.
			'				text-align:right;'.
			'			}'.
			'			.delta{'.
			'				text-align:center;'.
			'			}'.
			'		</style>'.
			'		<meta http-equiv="X-UA-Compatible" content="IE=Edge">'.
			'		<meta name="viewport" content="width=device-width, initial-scale=1.0">'.
			'		<!--<link type="text/css" href="style.css" rel="stylesheet"/>-->'.
			'		<!--<script src="script.js" type="application/javascript"></script>-->'.
			'		<script type="application/javascript">'.
			'			function loaded(){'.
			'				var c=document.getElementsByClassName("note");'.
			'				for(var i=c.length-1;i>-1;i--){'.
			'					c[i].parentNode.previousElementSibling.childNodes[4].textContent="Settings Changed";'.
			'				}'.
			'			}'.
			'		</script>'.
			'		<!--[if lt IE 9]><link type="text/css" href="old_ie.css" rel="stylesheet"/><![endif]-->'.
			'	</head>'.
			'	<body class="F" onload="loaded()">Temperature Format:'.
			'		<select onchange="this.parentNode.className=this.value">'.
			'			<option value="F">Fahrenheit</option>'.
			'			<option value="C">Celsius</option>'.
			'			<option value="K">Kelvin</option>'.
			'		</select><br/>'.
			'<table border="1"><thead><tr><th>Time</th><th>Duration</th><th>Temperature</th><th>Action</th><th>Note</th></tr></thead><tbody>';
		foreach($rows as $row){
			if ($row=='') continue;
			echo "<tr>";
			$cells=explode(" ",$row);
			echo '<td class="date">'.date("g:i A m-d-Y",$cells[0])."</td>";
			if($time==0)
				echo '<td class="delta">TBD</td>';
			else{
				$delta=$time-$cells[0];
				echo '<td class="delta">'.sprintf('%02d:%02d:%02d', ($delta/ 3600),($delta/ 60 % 60), $delta% 60)."</td>";
			}
			echo '<td class="temp"><span class="F">'
				.((($cells[2])*(9/5))+32).'°F</span><span class="C">'.
				($cells[2]).'°C</span><span class="K">'.
				($cells[2]+273.15).' K</span></td>';
			echo '<td class="act">';
			if ($cells[1]==0)
				echo "Cooling: ".($cells[3]==1?'A':'Ina').'ctive';
			else if ($cells[1]==1)
				echo "Heating: ".($cells[3]==0?'A':'Ina').'ctive'.($cells[3]==0?'; Auxillary: '.($cells[4]==0?'Off':'On'):'');
			else if ($cells[1]==2)
				echo "Copycat: ".($cells[3]==1?'Left':'Right').'; '.($cells[4]==1?'Left':'Right');
			echo "</td>";
			if($set==0||$set==$cells[5]){
				echo '<td>&nbsp;</td>';
			}
			else{
				echo '<td class="note">&nbsp;</td>';
			}
			echo "</tr>";
			$set=$cells[5];
			$time=$cells[0];
		}
		echo "</table>";
		$files=scandir('data');
		$i=0;
		foreach($files as $file){
			if(in_array($file,array(".","..")) || !str_contains($file,".txt"))
				continue;
			if($i > 0)
				echo " | ";
			echo '<a href="?page='.($i++).'">Page '.$i.'</a>';
		}
		echo "<br/>Showing page";
		if($page==-1)
			echo "s 1 and 2";
		else
			echo " $page";
		echo "</body></html>";
	}
	else{
		header('Content-type: text/plain');
		echo "No log file";
	}
}
die();
?>
