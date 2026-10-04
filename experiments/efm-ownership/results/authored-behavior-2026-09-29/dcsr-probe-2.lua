trigger.action.setUserFlag('DCSR_PROBE_2_READY',1)
env.info('PREPARED_BEHAVIOR owned_flag=DCSR_PROBE_2_READY authored_flag='..trigger.misc.getUserFlag('DCSR_PROBE_1_READY'))
