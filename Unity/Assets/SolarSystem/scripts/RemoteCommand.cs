using UnityEngine;
using System.Collections;
using System;

[System.Serializable]
public class RemoteCommand 
{
	public String target;

	public static RemoteCommand CreateFromJSON(string jsonString)
	{
		RemoteCommand cmd = null;

		try{
			cmd = JsonUtility.FromJson<RemoteCommand> (jsonString);
		}
		catch (System.Exception e ) {
			Debug.Log (@"Something went wrong " + e);
		}

		return cmd;
	}
}
