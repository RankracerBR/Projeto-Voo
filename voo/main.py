import simpy
import numpy as np
import pandas as pd
import streamlit as st
import datetime

# Parâmetros iniciais
NUM_DAYS = 100
NUM_ATTENDANTS = 3
AVG_PASSENGERS_PER_DAY = 10
AVG_SERVICE_TIME = 3  # horas

# Função para gerar a chegada de passageiros com base na distribuição normal
def generate_passenger_arrivals(env, num_days, avg_passengers_per_day, passenger_arrivals):
    for day in range(num_days):
        num_passengers = max(0, int(np.random.normal(avg_passengers_per_day, 2)))  # Gerando número de passageiros
        for i in range(num_passengers):
            arrival_time = np.random.uniform(0, 24)  # Passageiros chegando ao longo do dia
            current_time = env.now  # Tempo atual da simulação
            # Adicionando tempo de chegada no formato de hora e minuto
            passenger_arrivals.append(current_time + day * 24 + arrival_time)
            yield env.timeout(arrival_time)  # Simulate passage of time until next arrival
            env.process(passenger(env, current_time + day * 24 + arrival_time))

# Função para modelar o atendimento de passageiros
def passenger(env, arrival_time):
    if attendants is not None:
        with attendants.request() as request:  # Request an attendant
            yield request | env.timeout(0)  # Immediate check for available attendant
            if request.triggered:  # If attendant is available
                start_service = env.now
                service_time = max(0, np.random.normal(AVG_SERVICE_TIME, 1))  # Tempo de serviço variado
                yield env.timeout(service_time)  # Simulate the service time
                end_service = env.now
                attended_passengers.append((
                    arrival_time, start_service, end_service)
                )  # Log attended passenger
            else:  # If no attendant is available
                denied_passengers.append(arrival_time)  # Log denied passenger
    else:
        denied_passengers.append(arrival_time)  # If no attendants, deny passenger

def run_simulation(num_days, num_attendants, avg_passengers_per_day):
    global attendants, attended_passengers, denied_passengers
    attended_passengers = []
    denied_passengers = []
    env = simpy.Environment()
    attendants = simpy.Resource(
        env, capacity=num_attendants
        ) if num_attendants > 0 else None  # Initialize resources (attendants)
    passenger_arrivals = []
    env.process(generate_passenger_arrivals(
        env, num_days, 
        avg_passengers_per_day, passenger_arrivals)
        )
    env.run(until=num_days * 24)  # Run the simulation

    current_date = datetime.datetime.utcnow()  # Obter o tempo atual em UTC

    attended_df = pd.DataFrame(attended_passengers, 
                               columns=['Tempo de Chegada', 
                                        'Início do Atendimento', 
                                        'Final do Atendimento']
                               )
    if not attended_df.empty:
        # Convertendo o tempo de início do atendimento para a data atual
        attended_df['Início do Atendimento'] = attended_df['Início do Atendimento'].apply(lambda x: current_date + datetime.timedelta(hours=x))
        # Convertendo o tempo de final do atendimento para a data atual
        attended_df['Final do Atendimento'] = attended_df['Final do Atendimento'].apply(lambda x: current_date + datetime.timedelta(hours=x))
        # Convertendo o tempo de chegada para a data atual
        attended_df['Tempo de Chegada'] = attended_df['Tempo de Chegada'].apply(lambda x: current_date + datetime.timedelta(hours=x))

    denied_df = pd.DataFrame(denied_passengers, columns=['Tempo de Chegada'])
    if not denied_df.empty:
        # Convertendo o tempo de chegada para a data atual
        denied_df['Tempo de Chegada'] = denied_df['Tempo de Chegada'].apply(lambda x: current_date + datetime.timedelta(hours=x))
        # Convertendo para formato de data e hora
        denied_df['Tempo de Chegada'] = denied_df['Tempo de Chegada'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))

    utilization = (len(attended_df) * AVG_SERVICE_TIME) / (
        num_days * 24 * num_attendants) if num_attendants > 0 else 0

    if num_attendants == 0:
        st.write("### Não houve atendimento, pois o número de atendentes é 0.")
        return None, None, None
    
    return attended_df, denied_df, utilization

# Streamlit interface
st.title("Simulação de Atendimento de Passageiros")
num_days = st.slider("Número de dias", 10, 365, 100)
num_attendants = st.slider("Número de atendentes", 0, 10, 3)
avg_passengers_per_day = st.slider("Número médio de passageiros por dia", 1, 50, 10)
avg_service_time = st.slider("Tempo médio de serviço (horas)", 1, 5, 3)
if st.button("Run Simulation"):
    attended_df, denied_df, utilization = run_simulation(num_days, num_attendants, avg_passengers_per_day)
    
    if attended_df is not None:
        st.write("### Resultados da Simulação")
        st.write(f"Passageiros atendidos: {len(attended_df)}")
        st.write(f"Passageiros negados: {len(denied_df)}")
        st.write(f"Taxa de utilização dos atendentes: {utilization:.2%}")
        
        st.write("### Detalhes dos Passageiros Atendidos")
        st.dataframe(attended_df)
        
        st.write("### Detalhes dos Passageiros Negados")
        st.dataframe(denied_df)
